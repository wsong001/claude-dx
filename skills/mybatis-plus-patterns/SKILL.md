---
name: mybatis-plus-patterns
description: MyBatis-Plus 持久化模式：实体设计、Mapper/Service 分层、LambdaWrapper 查询、分页、批量操作、逻辑删除、自动填充、乐观锁。基于阿里巴巴 ORM 映射规约。
---

# MyBatis-Plus 持久化模式

适用于 Spring Boot + MyBatis-Plus 项目的数据访问层开发规范与最佳实践。

## 阿里巴巴 ORM 映射规约

### 强制规约

- 禁止使用 `SELECT *`，必须明确指定查询字段
- SQL 参数使用 `#{}`，禁止使用 `${}`（防止 SQL 注入）
- 布尔字段：数据库使用 `is_` 前缀（如 `is_deleted`），POJO 不加 `is` 前缀（如 `deleted`），通过映射配置转换
- 禁止用 `HashMap` 或 `Hashtable` 作为查询结果集输出，必须定义对应的 DO 类
- 必须定义 `resultMap` 进行字段与 DO 类的映射，不依赖隐式映射
- DAO 层异常使用 `catch(Exception e)` 并向上抛出，不在 DAO 层打印日志（日志在 Service 层记录）

### 推荐规约

- 表必备三字段：`id`（主键）、`gmt_create`（创建时间）、`gmt_modified`（更新时间）
- 表名、字段名使用小写字母加下划线，禁止以数字开头
- 字段值为非负数时使用 `UNSIGNED`
- `varchar` 长度不超过 5000，超过使用 `TEXT` 并独立表存储

## 实体设计

```java
@Data
@TableName("t_activity")
public class ActivityEntity {
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    @TableField("activity_name")
    private String activityName;

    @TableField("activity_type")
    private String activityType;

    @TableField("is_deleted")
    @TableLogic
    private Integer deleted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime gmtCreate;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime gmtModified;

    @Version
    private Integer version;
}
```

## 自动填充

```java
@Component
public class MetaObjectHandler implements com.baomidou.mybatisplus.core.handlers.MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "gmtCreate", LocalDateTime::now, LocalDateTime.class);
        this.strictInsertFill(metaObject, "gmtModified", LocalDateTime::now, LocalDateTime.class);
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "gmtModified", LocalDateTime::now, LocalDateTime.class);
    }
}
```

## Mapper 层

Mapper 继承 `BaseMapper`，用于简单 CRUD 操作：

```java
@Mapper
public interface ActivityMapper extends BaseMapper<ActivityEntity> {
    /**
     * 自定义复杂查询（多表关联等场景）
     */
    @Select("SELECT a.id, a.activity_name, a.activity_type " +
            "FROM t_activity a " +
            "INNER JOIN t_channel c ON a.channel_id = c.id " +
            "WHERE c.status = #{status}")
    List<ActivityEntity> selectByChannelStatus(@Param("status") String status);
}
```

启动类配置扫描：

```java
@SpringBootApplication
@MapperScan("com.example.app.mapper")
public class Application {}
```

## Service 层

Service 继承 `IService`，用于业务逻辑编排和批量操作：

```java
public interface ActivityService extends IService<ActivityEntity> {
    ActivityEntity getByName(String name);
    Page<ActivityEntity> pageByType(String type, int pageNum, int pageSize);
}

@Service
public class ActivityServiceImpl extends ServiceImpl<ActivityMapper, ActivityEntity>
        implements ActivityService {

    @Override
    public ActivityEntity getByName(String name) {
        return lambdaQuery()
                .eq(ActivityEntity::getActivityName, name)
                .one();
    }

    @Override
    public Page<ActivityEntity> pageByType(String type, int pageNum, int pageSize) {
        return lambdaQuery()
                .eq(StringUtils.isNotBlank(type), ActivityEntity::getActivityType, type)
                .orderByDesc(ActivityEntity::getGmtCreate)
                .page(new Page<>(pageNum, pageSize));
    }
}
```

### IService 命名约定

| 前缀 | 含义 | 示例 |
|------|------|------|
| `get` | 查询单条 | `getById()`, `getOne()` |
| `list` | 查询集合 | `list()`, `listByIds()` |
| `page` | 分页查询 | `page()` |
| `save` | 新增 | `save()`, `saveBatch()` |
| `update` | 更新 | `updateById()`, `updateBatchById()` |
| `remove` | 删除 | `removeById()`, `removeByIds()` |

## LambdaWrapper 查询

**始终优先使用 LambdaQueryWrapper / LambdaUpdateWrapper，禁止硬编码列名字符串。**

```java
// 条件查询
LambdaQueryWrapper<ActivityEntity> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(ActivityEntity::getActivityType, "promotion")
       .ge(ActivityEntity::getGmtCreate, startDate)
       .orderByDesc(ActivityEntity::getGmtCreate);
List<ActivityEntity> list = activityMapper.selectList(wrapper);

// 条件更新
LambdaUpdateWrapper<ActivityEntity> updateWrapper = new LambdaUpdateWrapper<>();
updateWrapper.eq(ActivityEntity::getId, activityId)
             .set(ActivityEntity::getActivityType, "campaign");
activityMapper.update(null, updateWrapper);

// 仅在 SET 子句包含特殊表达式时使用 UpdateWrapper
UpdateWrapper<ActivityEntity> specialWrapper = new UpdateWrapper<>();
specialWrapper.eq("id", activityId)
              .setSql("budget = budget - 1000");
activityMapper.update(null, specialWrapper);
```

### 条件构造技巧

```java
// 条件参数非空时才拼接（避免 if 判断）
wrapper.eq(StringUtils.isNotBlank(type), ActivityEntity::getActivityType, type)
       .like(StringUtils.isNotBlank(name), ActivityEntity::getActivityName, name);
```

## 分页配置

```java
@Configuration
public class MybatisPlusConfig {
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

分页查询：

```java
Page<ActivityEntity> page = new Page<>(pageNum, pageSize);
LambdaQueryWrapper<ActivityEntity> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(ActivityEntity::getActivityType, type);
Page<ActivityEntity> result = activityMapper.selectPage(page, wrapper);
```

## 批量操作

```java
// 批量新增（默认每批 1000 条）
activityService.saveBatch(entityList);

// 批量新增（自定义批次大小）
activityService.saveBatch(entityList, 500);

// 批量更新
activityService.updateBatchById(entityList);

// 批量新增或更新
activityService.saveOrUpdateBatch(entityList);
```

## 逻辑删除

全局配置：

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0
```

配置后，`selectList`、`update` 等方法自动追加 `WHERE deleted = 0`，`remove` 方法自动转为 `UPDATE SET deleted = 1`。

## 乐观锁

```java
@Configuration
public class MybatisPlusConfig {
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new OptimisticLockerInnerInterceptor());
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

使用时先查询再更新，确保 `version` 字段有值：

```java
ActivityEntity entity = activityMapper.selectById(id);
entity.setActivityName("updated");
activityMapper.updateById(entity);  // WHERE id = ? AND version = ?
```

## 自定义 SQL 与 Wrapper 结合

Mapper 中使用 `${ew.customSqlSegment}` 注入 Wrapper 条件：

```java
@Select("SELECT a.*, c.channel_name " +
        "FROM t_activity a " +
        "LEFT JOIN t_channel c ON a.channel_id = c.id " +
        "${ew.customSqlSegment}")
Page<ActivityVO> selectWithChannel(Page<?> page, @Param(Constants.WRAPPER) Wrapper<ActivityEntity> wrapper);
```

## 需要避免的问题

- 禁止在 `foreach` 循环中逐条调用 `insert`/`update`，使用批量操作
- 禁止用 `QueryWrapper` 硬编码列名字符串，使用 `LambdaQueryWrapper`
- 分页查询必须配置 `PaginationInnerInterceptor`，否则 `Page` 不生效
- 逻辑删除字段不要与 `unique` 索引冲突，需建立联合唯一索引包含删除标记
- 乐观锁更新前必须先查询获取 `version` 值，否则更新无效

**核心理念**：Mapper 层处理数据访问，Service 层编排业务逻辑。优先使用 Lambda 表达式保证类型安全，批量操作代替循环单条操作，逻辑删除代替物理删除。
