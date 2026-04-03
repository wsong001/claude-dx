---
name: springboot-patterns
description: Spring Boot 架构模式：REST API 设计、分层架构、数据访问、缓存、异步处理、全局异常处理、日志、限流、可观测性。
---

# Spring Boot 开发模式

适用于生产级 Spring Boot 服务的架构和 API 模式。

## REST API 结构

```java
@RestController
@RequestMapping("/api/markets")
@Validated
class MarketController {
    private final MarketService marketService;

    MarketController(MarketService marketService) {
        this.marketService = marketService;
    }

    @GetMapping
    ResponseEntity<Page<MarketResponse>> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Page<Market> markets = marketService.list(PageRequest.of(page, size));
        return ResponseEntity.ok(markets.map(MarketResponse::from));
    }

    @PostMapping
    ResponseEntity<MarketResponse> create(@Valid @RequestBody CreateMarketRequest request) {
        Market market = marketService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(MarketResponse.from(market));
    }
}
```

## Repository 模式（Spring Data JPA）

```java
public interface MarketRepository extends JpaRepository<MarketEntity, Long> {
    @Query("select m from MarketEntity m where m.status = :status order by m.volume desc")
    List<MarketEntity> findActive(@Param("status") MarketStatus status, Pageable pageable);
}
```

## Service 层与事务管理

```java
@Service
public class MarketService {
    private final MarketRepository repo;

    public MarketService(MarketRepository repo) {
        this.repo = repo;
    }

    @Transactional
    public Market create(CreateMarketRequest request) {
        MarketEntity entity = MarketEntity.from(request);
        MarketEntity saved = repo.save(entity);
        return Market.from(saved);
    }
}
```

## DTO 与参数校验

```java
public record CreateMarketRequest(
        @NotBlank @Size(max = 200) String name,
        @NotBlank @Size(max = 2000) String description,
        @NotNull @FutureOrPresent Instant endDate,
        @NotEmpty List<@NotBlank String> categories) {}

public record MarketResponse(Long id, String name, MarketStatus status) {
    static MarketResponse from(Market market) {
        return new MarketResponse(market.id(), market.name(), market.status());
    }
}
```

## 全局异常处理

```java
@ControllerAdvice
class GlobalExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult().getFieldErrors().stream()
                .map(e -> e.getField() + ": " + e.getDefaultMessage())
                .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest().body(ApiError.validation(message));
    }

    @ExceptionHandler(AccessDeniedException.class)
    ResponseEntity<ApiError> handleAccessDenied() {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiError.of("Forbidden"));
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<ApiError> handleGeneric(Exception ex) {
        // 记录未预期的异常堆栈
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiError.of("Internal server error"));
    }
}
```

## 缓存

需要在配置类上添加 `@EnableCaching`。

```java
@Service
public class MarketCacheService {
    private final MarketRepository repo;

    public MarketCacheService(MarketRepository repo) {
        this.repo = repo;
    }

    @Cacheable(value = "market", key = "#id")
    public Market getById(Long id) {
        return repo.findById(id)
                .map(Market::from)
                .orElseThrow(() -> new EntityNotFoundException("Market not found"));
    }

    @CacheEvict(value = "market", key = "#id")
    public void evict(Long id) {}
}
```

## 异步处理

需要在配置类上添加 `@EnableAsync`。

```java
@Service
public class NotificationService {
    @Async
    public CompletableFuture<Void> sendAsync(Notification notification) {
        // 发送邮件/短信
        return CompletableFuture.completedFuture(null);
    }
}
```

## 日志（SLF4J）

```java
@Service
public class ReportService {
    private static final Logger log = LoggerFactory.getLogger(ReportService.class);

    public Report generate(Long marketId) {
        log.info("generate_report marketId={}", marketId);
        try {
            // 业务逻辑
        } catch (Exception ex) {
            log.error("generate_report_failed marketId={}", marketId, ex);
            throw ex;
        }
        return new Report();
    }
}
```

## 请求日志过滤器

```java
@Component
public class RequestLoggingFilter extends OncePerRequestFilter {
    private static final Logger log = LoggerFactory.getLogger(RequestLoggingFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        long start = System.currentTimeMillis();
        try {
            filterChain.doFilter(request, response);
        } finally {
            long duration = System.currentTimeMillis() - start;
            log.info("req method={} uri={} status={} durationMs={}",
                    request.getMethod(), request.getRequestURI(), response.getStatus(), duration);
        }
    }
}
```

## 分页与排序

```java
PageRequest page = PageRequest.of(pageNumber, pageSize, Sort.by("createdAt").descending());
Page<Market> results = marketService.list(page);
```

## 外部调用重试

```java
public <T> T withRetry(Supplier<T> supplier, int maxRetries) {
    int attempts = 0;
    while (true) {
        try {
            return supplier.get();
        } catch (Exception ex) {
            attempts++;
            if (attempts >= maxRetries) {
                throw ex;
            }
            try {
                Thread.sleep((long) Math.pow(2, attempts) * 100L);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                throw ex;
            }
        }
    }
}
```

## 限流（Filter + Bucket4j）

**安全提示**：`X-Forwarded-For` 请求头默认不可信，客户端可以伪造。仅在以下条件下使用转发头：
1. 应用部署在受信任的反向代理（nginx、AWS ALB 等）之后
2. 已注册 `ForwardedHeaderFilter` Bean
3. 已配置 `server.forward-headers-strategy=NATIVE` 或 `FRAMEWORK`
4. 代理已配置为覆盖（而非追加）`X-Forwarded-For` 头

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {
    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        String clientIp = request.getRemoteAddr();
        Bucket bucket = buckets.computeIfAbsent(clientIp,
                k -> Bucket.builder()
                        .addLimit(Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1))))
                        .build());
        if (bucket.tryConsume(1)) {
            filterChain.doFilter(request, response);
        } else {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
        }
    }
}
```

## 定时任务

使用 Spring 的 `@Scheduled` 或集成消息队列（如 Kafka、SQS、RabbitMQ）。处理器必须保证幂等性和可观测性。

## 可观测性

- 结构化日志（JSON）：通过 Logback encoder 实现
- 指标监控：Micrometer + Prometheus/OTel
- 链路追踪：Micrometer Tracing + OpenTelemetry 或 Brave

## 生产环境默认配置

- 优先使用构造器注入，禁止字段注入
- 启用 `spring.mvc.problemdetails.enabled=true` 支持 RFC 7807 错误格式（Spring Boot 3+）
- 根据负载配置 HikariCP 连接池大小和超时时间
- 只读查询使用 `@Transactional(readOnly = true)`
- 通过 `@NonNull` 和 `Optional` 强制空值安全

**核心理念**：Controller 保持轻量，Service 专注业务，Repository 简单直接，异常统一处理。优先保证可维护性和可测试性。
