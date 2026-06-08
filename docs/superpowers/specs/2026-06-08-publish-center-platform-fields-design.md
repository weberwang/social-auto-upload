# 发布中心平台字段体系设计

## 1. 背景

当前发布中心已经支持多平台视频/图文发布，但字段模型仍以单页签平铺字段为主，导致以下问题：

- 公共字段与平台专属字段混杂在同一状态对象中，字段语义冲突明显。
- 页面组件边界不清晰，平台差异持续堆积在 `PublishCenter.vue` 中。
- 草稿恢复、跨平台复制、内容类型切换都依赖大量手工清空逻辑，容易产生脏数据。
- 历史 Web 接口、bridge、CLI、uploader 的字段演进没有统一约束，前后端经常互相污染。

本设计用于统一发布中心的平台字段体系，并确定“全平台统一设计、先实现视频号”的首阶段落地方式。

## 2. 目标

本次设计目标如下：

- 建立统一的“基础字段 + 平台增强字段”模型。
- 把视频/图文公共输入与平台专属输入拆分为独立组件。
- 明确全平台视频/图文字段清单。
- 统一草稿恢复、跨平台复制、提交映射、内容类型切换的规则。
- 先完成视频号视频/图文首阶段实现设计，包含显示层组件、历史 Web 接口、bridge、CLI、uploader 的联动方案。

## 3. 非目标

- 本次不新增 B 站图文/专栏投稿入口。
- 本次不要求首阶段同时实现抖音、快手、小红书的缺失字段，只要求在设计上纳入字段体系。
- 本次不改造历史数据库结构；草稿仍按前端工作区快照存储，但恢复时要做模型迁移。

## 4. 平台字段清单

### 4.1 基础视频字段

所有支持视频的平台共享以下字段：

- 标题
- 视频素材
- 视频描述/简介
- 话题
- 定时发布开关
- 定时配置：每天发布数量、每天发布时间、开始天数

### 4.2 基础图文字段

所有支持图文的平台共享以下字段：

- 标题
- 图片素材
- 图文正文
- 话题
- 定时发布开关
- 定时配置：每天发布数量、每天发布时间、开始天数

### 4.3 平台增强字段

#### 视频号

视频：

- 短标题
- 声明原创
- 原创类型
- 内容声明
- 合集
- 横版封面（4:3）
- 竖版封面（3:4）
- 仅保存草稿

图文：

- 声明原创
- 原创类型
- 内容声明
- 合集
- 仅保存草稿
- 短标题（仅在页面存在稳定入口时展示）
- 图文封面（仅在页面存在稳定入口时展示）

#### 抖音

视频：

- 商品名称
- 商品链接
- 横版封面
- 竖版封面

图文：

- 暂无平台专属字段，首版仅使用基础图文字段

#### 快手

视频：

- 封面图

图文：

- 暂无平台专属字段，首版仅使用基础图文字段

#### 小红书

视频：

- 封面图

图文：

- 暂无平台专属字段，首版仅使用基础图文字段

#### B 站

视频：

- 简介
- 分区

图文：

- 本次不设计入口，不提供字段

## 5. 前端统一字段模型

单个发布页签状态重构为“流程信息 + 基础字段 + 平台增强字段”三层：

```ts
type PublishTabState = {
  name: string
  label: string
  selectedPlatform: 1 | 2 | 3 | 4 | 5
  contentType: 'video' | 'image_text'
  materials: {
    fileList: PublishFile[]
    displayFileList: DisplayFile[]
  }
  accounts: {
    selectedAccountIds: Array<number | string>
  }
  baseFields: {
    title: string
    description: string
    noteContent: string
    topics: string[]
    scheduleEnabled: boolean
    videosPerDay: number
    dailyTimes: string[]
    startDays: number
  }
  platformFields: {
    douyin: {
      productTitle: string
      productLink: string
      thumbnailLandscapePath: string
      thumbnailPortraitPath: string
    }
    kuaishou: {
      thumbnailPath: string
    }
    xiaohongshu: {
      thumbnailPath: string
    }
    tencent: {
      shortTitle: string
      collectionName: string
      declareOriginal: boolean
      originalType: string
      contentDeclaration: string
      thumbnailLandscapePath: string
      thumbnailPortraitPath: string
      noteCoverPath: string
      isDraft: boolean
    }
    bilibili: {
      description: string
      tid: number | null
    }
  }
  publishStatus: {
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
  } | null
  publishing: boolean
}
```

### 5.1 设计约束

- `baseFields.description` 仅表示通用视频描述。
- `platformFields.bilibili.description` 仅表示 B 站视频简介，不能复用 `baseFields.description`。
- `isOriginal` 不再作为顶层通用字段，归属到平台增强字段。
- 平台增强字段必须始终按平台分组保存，禁止重新回退到顶层平铺命名。

## 6. 组件拆分方案

发布中心前端拆为“基础内容类型组件 + 平台增强组件 + 装配层”三层。

### 6.1 基础内容类型组件

- `BaseVideoFields.vue`
  - 负责标题、描述、话题、定时配置
- `BaseImageTextFields.vue`
  - 负责标题、正文、话题、定时配置

### 6.2 平台增强组件

- `DouyinVideoEnhancement.vue`
  - 商品名称、商品链接、横版封面、竖版封面
- `KuaishouVideoEnhancement.vue`
  - 封面图
- `XiaohongshuVideoEnhancement.vue`
  - 封面图
- `TencentVideoEnhancement.vue`
  - 短标题、声明原创、原创类型、内容声明、合集、双封面、仅保存草稿
- `TencentImageTextEnhancement.vue`
  - 声明原创、原创类型、内容声明、合集、仅保存草稿
  - 短标题与图文封面只在页面真实存在稳定控件后再展示
- `BilibiliVideoEnhancement.vue`
  - 简介、分区

### 6.3 装配层

- `PublishCenter.vue` 只负责：
  - 页签管理
  - 平台与内容类型选择
  - 基础组件装配
  - 平台增强组件装配
  - 素材、账号、草稿、提交流程调度

这样可以把平台差异从主视图中剥离，避免 `PublishCenter.vue` 继续膨胀。

## 7. 提交映射与后端结构

前端不再把整份页签状态直接平铺提交，而是先映射成“基础字段 + 平台增强字段 + 流程字段”的统一请求结构。

建议请求结构如下：

```json
{
  "type": 2,
  "contentType": "image_text",
  "baseFields": {
    "title": "标题",
    "description": "",
    "noteContent": "正文",
    "tags": ["话题1"],
    "enableTimer": 1,
    "videosPerDay": 2,
    "dailyTimes": ["10:00", "18:00"],
    "startDays": 0
  },
  "platformFields": {
    "tencent": {
      "shortTitle": "短标题",
      "declareOriginal": true,
      "originalType": "生活",
      "contentDeclaration": "无需声明",
      "collectionName": "默认合集",
      "thumbnailLandscapePath": "",
      "thumbnailPortraitPath": "",
      "noteCoverPath": "",
      "isDraft": false
    }
  },
  "fileList": ["a.png", "b.png"],
  "accountList": ["tencent_creator.json"]
}
```

### 7.1 历史 Web 接口层

- `parse_web_publish_request`
  - 解析统一请求结构
  - 在 Flask 边界完成字段标准化
- `validate_web_publish_request`
  - 按 `platform + contentType` 校验平台增强字段
- `dispatch_web_publish_request`
  - 只负责按平台和内容类型路由

### 7.2 bridge / CLI / uploader 层

- `sau_bridge.publish`
  - 为视频号补充增强字段透传
- `sau_cli.py`
  - 增加与视频号增强字段对应的请求对象与调用参数
- `uploader/tencent_uploader/main.py`
  - 真正消费这些字段并执行页面自动化

## 8. 草稿恢复与复制规则

### 8.1 旧草稿恢复

恢复旧草稿时按以下规则迁移：

- 旧顶层 `description`
  - 若当前为 B 站视频，迁移到 `platformFields.bilibili.description`
  - 否则迁移到 `baseFields.description`
- 旧顶层 `noteContent`
  - 迁移到 `baseFields.noteContent`
- 旧顶层 `selectedTopics`
  - 迁移到 `baseFields.topics`
- 旧顶层 `productTitle/productLink`
  - 迁移到 `platformFields.douyin`
- 旧顶层 `isDraft`
  - 迁移到 `platformFields.tencent.isDraft`
- 旧顶层 `bilibiliTid`
  - 迁移到 `platformFields.bilibili.tid`

### 8.2 跨平台复制

- 只复制 `baseFields`
- 只保留目标平台对应的 `platformFields[目标平台]`
- 其余平台增强字段全部清空

### 8.3 同平台复制

- 同时复制 `baseFields` 和当前平台对应的 `platformFields`

### 8.4 切换内容类型

- 基础层只清理不兼容字段
- 平台增强字段按 `platform + contentType` 精确清理
- 禁止继续在主页面里散落手工清空逻辑

## 9. 视频号首阶段实现边界

本项目采用“全平台统一设计、先实现视频号”的推进方式。

### 9.1 前端

需要落地：

- `BaseVideoFields.vue`
- `BaseImageTextFields.vue`
- `TencentVideoEnhancement.vue`
- `TencentImageTextEnhancement.vue`
- 新字段模型驱动的草稿恢复、跨平台复制、发布校验、payload 组装

### 9.2 历史 Web 接口

需要落地：

- `/postVideo` 支持视频号新增字段
- 旧请求兼容到新结构

### 9.3 CLI / bridge

需要落地：

- 视频号视频增强字段透传
- 视频号图文增强字段透传
- 定时配置透传

### 9.4 uploader

需要落地视频号视频全字段接线，并完成 `TencentNote` 的关键缺口：

- 切换到图文发布模式
- 上传图文图片
- 填写图文标题和话题
- 填写图文正文（若页面存在正文输入）
- 图文定时发布
- 图文原创声明
- 图文内容声明
- 图文合集
- 图文草稿保存

### 9.5 暂不实现

- 抖音、快手、小红书缺失字段的实际接线
- B 站新字段扩展
- B 站图文入口

## 10. 风险与处理策略

### 10.1 视频号图文页面控件不稳定

风险：

- 图文模式入口、上传控件、原创声明、合集等控件可能与视频页差异明显。

处理：

- 先做页面结构探测，再选择最稳定的 locator。
- 对“可选字段”采用“存在则填写，不存在则跳过”的策略。
- 对“必须字段”在自动化前做显式检查并记录诊断日志。

### 10.2 新旧草稿并存导致脏数据

风险：

- 平铺字段草稿恢复到新模型时，平台字段可能错位。

处理：

- 统一在草稿恢复入口做迁移。
- 禁止新模型直接读取旧字段。

### 10.3 前端主视图继续膨胀

风险：

- 若仍把平台字段直接写回 `PublishCenter.vue`，本次重构目标会失效。

处理：

- 平台特有显示逻辑必须下沉到增强组件。
- 主视图只允许保留流程编排代码。

## 11. 测试与验收

### 11.1 前端测试

- 平台增强字段显示规则
- 草稿恢复迁移
- 跨平台复制字段清理
- 请求 payload 映射

### 11.2 后端测试

- 历史 Web 接口参数解析
- 平台/内容类型校验
- 视频号视频/图文分发

### 11.3 bridge / CLI 测试

- 视频号增强字段透传
- 定时字段透传

### 11.4 uploader 测试

- `TencentNote` 模式切换
- 图片上传
- 标题/正文/话题填写
- 定时设置
- 原创声明 / 内容声明 / 合集

### 11.5 手工验收

- 视频号视频立即发布
- 视频号视频定时发布
- 视频号图文立即发布
- 视频号图文定时发布
- 视频号视频草稿
- 视频号图文草稿

## 12. 结论

本设计将发布中心从“顶层平铺字段 + 主页面堆分支”演进为“基础内容类型层 + 平台增强层 + 统一映射层”的结构。这样既能承接全平台字段体系，又能把第一阶段实现聚焦在视频号，避免一次性同时重构所有平台执行链路。
