---
name: java-coding-standards
description: Java 编码规范（Spring Boot 服务）：命名、OOP、不可变性、集合、并发、异常、日志、Spring Boot 分层、MySQL。基于阿里巴巴 Java 开发手册。
---

# Java 编码规范

适用于 Spring Boot 服务的 Java（17+）编码规范，基于阿里巴巴 Java 开发手册。

## 核心原则

- 清晰优于巧妙
- 默认不可变，减少共享可变状态
- 快速失败，提供有意义的异常信息
- 命名和包结构保持一致

## 命名规范

- 禁止使用拼音与英文混合命名，禁止纯拼音命名（国际通用名称如 alibaba、taobao 除外）
- 类名使用 UpperCamelCase，但 DO/BO/DTO/VO/PO 等除外（如 `UserDTO`、`OrderVO`）
- 方法名、参数名、成员变量使用 lowerCamelCase
- 常量使用 UPPER_SNAKE_CASE
- 抽象类以 `Abstract` 或 `Base` 开头，异常类以 `Exception` 结尾，测试类以被测类名 + `Test` 结尾
- 包名统一使用小写，点分隔符之间有且仅有一个自然语义的英语单词
- 枚举类名带 `Enum` 后缀，成员名全大写，下划线分隔

```java
public class MarketService {}
public record Money(BigDecimal amount, Currency currency) {}

private final MarketRepository marketRepository;
public Market findBySlug(String slug) {}

private static final int MAX_PAGE_SIZE = 100;
```

## OOP 规约

- 避免通过对象引用访问类的静态变量或方法，直接用类名访问
- 所有覆写方法必须加 `@Override` 注解
- 外部正在调用的接口，不允许直接修改方法签名，应通过新增方法实现过渡
- `Object` 的 `equals` 方法容易 NPE，应使用常量或确定非空的对象调用 `equals`
- 所有包装类对象之间的值比较使用 `equals` 方法，禁止用 `==`
- 构造方法中禁止加入业务逻辑，初始化逻辑放在 `init` 方法中
- POJO 类必须重写 `toString` 方法

## 不可变性

- 优先使用 record 和 final 字段
- 只提供 getter，不提供 setter

```java
public record MarketDto(Long id, String name, MarketStatus status) {}

public class Market {
    private final Long id;
    private final String name;
}
```

## 集合处理

- 集合初始化时尽量指定大小，避免扩容开销
- 使用 `Map` 的 `entrySet` 遍历而非 `keySet`（后者多一次查询）
- 禁止在 `foreach` 循环中对集合进行 `add`/`remove`，使用 `Iterator` 或 `removeIf`
- 集合转数组使用 `toArray(new String[0])`，禁止使用无参 `toArray()`
- `Arrays.asList()` 返回的是不可修改列表，不能执行 `add`/`remove`
- `ArrayList` 的 `subList` 返回的是内部类，不可强转为 `ArrayList`，对子列表的修改会影响原列表

```java
Map<String, Object> map = new HashMap<>(16);
List<String> list = new ArrayList<>(expectedSize);
```

## Stream 最佳实践

- 用 Stream 做数据转换，保持管道简短
- 避免复杂嵌套 Stream，复杂逻辑优先用循环保证可读性

```java
List<String> names = markets.stream()
    .map(Market::name)
    .filter(Objects::nonNull)
    .toList();
```

## Optional 用法

- find* 方法返回 Optional
- 使用 map/flatMap 代替 get()

```java
Optional<Market> market = marketRepository.findBySlug(slug);

return market
    .map(MarketResponse::from)
    .orElseThrow(() -> new EntityNotFoundException("Market not found"));
```

## 泛型与类型安全

- 禁止使用原始类型，必须声明泛型参数
- 可复用工具方法优先使用有界泛型

```java
public <T extends Identifiable> Map<Long, T> indexById(Collection<T> items) { ... }
```

## 并发处理

- 线程池禁止使用 `Executors` 创建，必须通过 `ThreadPoolExecutor` 显式指定参数
- `SimpleDateFormat` 线程不安全，禁止定义为 `static` 变量；推荐使用 `DateTimeFormatter`
- 对多个资源加锁时保持一致的加锁顺序，避免死锁
- 并发修改同一记录时使用乐观锁（版本号机制），行级悲观锁仅用于短事务

```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    corePoolSize, maxPoolSize, keepAliveTime, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(queueCapacity),
    new ThreadFactoryBuilder().setNameFormat("biz-pool-%d").build(),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

## 异常处理

- 领域错误使用非受检异常，技术异常包装后附带上下文信息
- 创建领域专属异常类（如 `MarketNotFoundException`）
- 避免宽泛的 `catch (Exception ex)`，除非是统一日志/重抛的场景
- 空 catch 块 → 记录日志并处理或重抛

```java
throw new MarketNotFoundException(slug);
```

## 控制语句

- `if/else/for/while/do` 语句必须使用大括号，即使只有一行
- 三目运算符中的高级别条件必须加括号
- 推荐使用卫语句（guard clause）减少嵌套层级
- `switch` 语句的每个 `case` 要么通过 `break`/`return` 终止，要么注释说明 fallthrough
- `switch` 必须包含 `default` 分支

## 空值处理

- 仅在不可避免时接受 `@Nullable`，其他情况使用 `@NonNull`
- 输入参数使用 Bean Validation（`@NotNull`、`@NotBlank`）校验

## 日志规范

```java
private static final Logger log = LoggerFactory.getLogger(MarketService.class);
log.info("fetch_market slug={}", slug);
log.error("failed_fetch_market slug={}", slug, ex);
```

## 注释规约

- 类、类属性、类方法使用 Javadoc 规范（`/** */`），禁止使用 `//` 替代
- 所有抽象方法（包括接口方法）必须使用 Javadoc 注释，说明返回值、参数、异常
- 方法内的单行注释使用 `//`，放在被注释语句的上方，与代码对齐
- 已被标记为 `@Deprecated` 的方法必须注释说明替代方案
- 禁止注释掉的代码残留在代码库中，直接删除（版本控制可追溯）

## 格式与风格

- 统一使用 2 或 4 空格缩进（跟随项目标准）
- 每个文件只包含一个 public 顶级类型
- 方法保持简短聚焦，复杂逻辑提取为辅助方法
- 成员排列顺序：常量 → 字段 → 构造方法 → public 方法 → protected 方法 → private 方法

## 需要避免的代码坏味道

- 参数过多 → 使用 DTO 或 Builder 模式
- 嵌套过深 → 提前 return
- 魔法数字 → 定义命名常量
- 静态可变状态 → 使用依赖注入

## Spring Boot 分层规范

- Controller 层只做参数校验和结果封装，禁止包含业务逻辑
- Service 层负责业务逻辑编排，单个方法不超过 80 行
- `@Transactional` 注解仅加在需要事务的方法上，避免大事务；只读查询使用 `@Transactional(readOnly = true)`
- 禁止在 Controller 层直接注入 Repository，必须通过 Service 层调用
- 配置项统一使用 `@ConfigurationProperties` 绑定，禁止散落的 `@Value`
- REST API 返回统一响应结构，包含 `code`、`message`、`data` 字段
- 接口入参使用 `@Valid` + Bean Validation 注解校验

```java
@Data
public class ApiResponse<T> {
    private int code;
    private String message;
    private T data;
}

@PostMapping("/users")
public ApiResponse<UserVO> createUser(@Valid @RequestBody CreateUserRequest request) {
    return ApiResponse.success(userService.createUser(request));
}
```

**核心理念**：代码应当意图明确、类型安全、可观测。优先优化可维护性，除非有性能瓶颈的实证，否则不做微优化。
