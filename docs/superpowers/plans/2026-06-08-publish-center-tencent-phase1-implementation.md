# 发布中心视频号首阶段 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成发布中心“统一字段模型 + 视频号首阶段落地”，打通视频号视频/图文的显示层、历史 Web 接口、CLI bridge 与 uploader 链路。

**Architecture:** 前端先把发布中心从“顶层平铺字段”重构为“基础字段 + 平台增强字段”模型，再通过 `PlatformEnhancementHost` 装配视频号增强组件。后端保留历史 `/postVideo` 入口，但在解析层接入统一请求结构，并把视频号增强字段透传到 `sau_bridge.publish`、`sau_cli.py` 与 `TencentVideo` / `TencentNote`。

**Tech Stack:** Vue 3、Element Plus、Node test、Flask、Python unittest、Playwright uploader、现有 `sau_bridge` / `sau_cli` / `uploader/tencent_uploader`

---

## 文件结构

### 新增文件

- `sau_frontend/src/constants/publishTabState.js`
  - 发布中心统一字段模型、默认值、迁移与清理规则
- `sau_frontend/src/constants/publishPayload.js`
  - 把新模型映射为历史 `/postVideo` 请求
- `sau_frontend/src/components/publish/BaseVideoFields.vue`
  - 视频基础字段组件
- `sau_frontend/src/components/publish/BaseImageTextFields.vue`
  - 图文基础字段组件
- `sau_frontend/src/components/publish/PlatformEnhancementHost.vue`
  - 平台增强组件装配器
- `sau_frontend/src/components/publish/TencentVideoEnhancement.vue`
  - 视频号视频增强字段组件
- `sau_frontend/src/components/publish/TencentImageTextEnhancement.vue`
  - 视频号图文增强字段组件
- `sau_frontend/tests/publish-tab-state.test.js`
  - 新模型迁移、切换、复制规则测试
- `sau_frontend/tests/publish-payload.test.js`
  - payload 映射测试
- `tests/test_tencent_note_publish.py`
  - `TencentNote` 关键链路测试

### 修改文件

- `sau_frontend/src/views/PublishCenter.vue`
  - 接入新模型和组件装配
- `sau_frontend/src/constants/publishPlatforms.js`
  - 只保留平台能力矩阵与平台文案，不再承载大块页签状态
- `sau_frontend/src/constants/publishTabCopy.js`
  - 改为基于新模型复制
- `sau_frontend/src/constants/publishDrafts.js`
  - 改为基于新模型做草稿恢复迁移
- `sau_frontend/tests/publish-tab-copy.test.js`
  - 更新为新模型断言
- `myUtils/web_publish.py`
  - 解析统一请求结构并透传视频号增强字段
- `tests/test_publish_endpoints.py`
  - 补视频号增强字段请求分发测试
- `sau_bridge/publish.py`
  - 补视频号视频/图文增强字段解析
- `tests/test_sau_bridge_publish.py`
  - 补 bridge 参数测试
- `sau_cli.py`
  - 补视频号视频/图文请求对象与分发字段
- `tests/test_sau_browser_cli.py`
  - 补 CLI 参数与分发测试
- `uploader/tencent_uploader/main.py`
  - 完成 `TencentNote` 发布逻辑并补视频号增强字段接线

### 责任边界

- `publishTabState.js` 只管状态模型，不管接口拼装。
- `publishPayload.js` 只做请求映射，不承载页面交互。
- 基础组件只消费 `baseFields`，平台增强组件只消费 `platformFields.tencent`。
- `myUtils/web_publish.py` 只做解析/校验/分发，不做页面自动化。
- `sau_bridge.publish` 与 `sau_cli.py` 只做字段透传，不重复业务判定。
- `TencentNote` 只做视频号图文页面自动化。

## 先锁定的实施决策

- 第一阶段只实现视频号，其他平台只完成设计落点，不接真实自动化。
- `/postVideo` 兼容旧请求，但前端新提交统一走 `baseFields + platformFields`。
- `B站图文` 不纳入本计划。
- 视频号图文中的“短标题”和“图文封面”只有页面存在稳定控件时才接线，否则第一阶段不显示、不透传。
- `声明原创 / 原创类型 / 内容声明 / 合集` 统一视为“可选但应尽量填写”的平台增强字段；页面无入口时记录日志并跳过，不阻断发布。

## Task 1: 建立发布中心统一字段模型与迁移规则

**Files:**
- Create: `sau_frontend/src/constants/publishTabState.js`
- Modify: `sau_frontend/src/constants/publishPlatforms.js`
- Modify: `sau_frontend/src/constants/publishTabCopy.js`
- Modify: `sau_frontend/src/constants/publishDrafts.js`
- Create: `sau_frontend/tests/publish-tab-state.test.js`
- Modify: `sau_frontend/tests/publish-tab-copy.test.js`

- [ ] **Step 1: 先写失败测试，锁定新模型、旧草稿迁移和跨平台复制规则**

```js
import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createDefaultPublishTabState,
  migrateLegacyPublishTab,
  copyPublishTabToPlatform
} from '../src/constants/publishTabState.js'

test('旧 B站视频草稿恢复时应把 description 迁移到 bilibili 平台字段', () => {
  const migrated = migrateLegacyPublishTab({
    selectedPlatform: 5,
    contentType: 'video',
    description: 'B站简介',
    bilibiliTid: 17
  })

  assert.equal(migrated.baseFields.description, '')
  assert.equal(migrated.platformFields.bilibili.description, 'B站简介')
  assert.equal(migrated.platformFields.bilibili.tid, 17)
})

test('跨平台复制到视频号图文时应清空 B站和抖音专属字段，只保留基础字段', () => {
  const copied = copyPublishTabToPlatform({
    ...createDefaultPublishTabState(),
    selectedPlatform: 3,
    contentType: 'video',
    baseFields: { title: '标题', description: '视频描述', noteContent: '', topics: ['测试'], scheduleEnabled: false, videosPerDay: 1, dailyTimes: ['10:00'], startDays: 0 },
    platformFields: {
      douyin: { productTitle: '商品', productLink: 'https://example.com', thumbnailLandscapePath: 'a.png', thumbnailPortraitPath: 'b.png' },
      kuaishou: { thumbnailPath: '' },
      xiaohongshu: { thumbnailPath: '' },
      tencent: { shortTitle: '', collectionName: '', declareOriginal: false, originalType: '', contentDeclaration: '', thumbnailLandscapePath: '', thumbnailPortraitPath: '', noteCoverPath: '', isDraft: false },
      bilibili: { description: '', tid: null }
    }
  }, 2, 4)

  assert.equal(copied.selectedPlatform, 2)
  assert.equal(copied.platformFields.douyin.productTitle, '')
  assert.equal(copied.platformFields.tencent.isDraft, false)
  assert.deepEqual(copied.baseFields.topics, ['测试'])
})
```

- [ ] **Step 2: 运行测试，确认新模型文件尚不存在**

Run: `cd sau_frontend && node --test tests/publish-tab-state.test.js tests/publish-tab-copy.test.js`
Expected: FAIL，报 `Cannot find module '../src/constants/publishTabState.js'` 或导出不存在

- [ ] **Step 3: 写最小状态模型与迁移函数**

```js
export function createDefaultPublishTabState() {
  return {
    name: 'tab1',
    label: '发布1',
    selectedPlatform: 1,
    contentType: 'video',
    materials: {
      fileList: [],
      displayFileList: []
    },
    accounts: {
      selectedAccountIds: []
    },
    baseFields: {
      title: '',
      description: '',
      noteContent: '',
      topics: [],
      scheduleEnabled: false,
      videosPerDay: 1,
      dailyTimes: ['10:00'],
      startDays: 0
    },
    platformFields: {
      douyin: {
        productTitle: '',
        productLink: '',
        thumbnailLandscapePath: '',
        thumbnailPortraitPath: ''
      },
      kuaishou: {
        thumbnailPath: ''
      },
      xiaohongshu: {
        thumbnailPath: ''
      },
      tencent: {
        shortTitle: '',
        collectionName: '',
        declareOriginal: false,
        originalType: '',
        contentDeclaration: '',
        thumbnailLandscapePath: '',
        thumbnailPortraitPath: '',
        noteCoverPath: '',
        isDraft: false
      },
      bilibili: {
        description: '',
        tid: null
      }
    },
    publishStatus: null,
    publishing: false
  }
}
```

- [ ] **Step 4: 把复制与草稿恢复入口改成新模型**

```js
export function migrateLegacyPublishTab(rawTab) {
  const tab = createDefaultPublishTabState()
  const selectedPlatform = Number(rawTab?.selectedPlatform) || tab.selectedPlatform
  tab.selectedPlatform = selectedPlatform
  tab.contentType = rawTab?.contentType === 'image_text' ? 'image_text' : 'video'
  tab.baseFields.title = typeof rawTab?.title === 'string' ? rawTab.title : ''
  tab.baseFields.noteContent = typeof rawTab?.noteContent === 'string' ? rawTab.noteContent : ''
  tab.baseFields.topics = Array.isArray(rawTab?.selectedTopics) ? rawTab.selectedTopics : []

  if (selectedPlatform === 5 && tab.contentType === 'video') {
    tab.platformFields.bilibili.description = typeof rawTab?.description === 'string' ? rawTab.description : ''
    tab.platformFields.bilibili.tid = Number.isInteger(rawTab?.bilibiliTid) ? rawTab.bilibiliTid : null
  } else {
    tab.baseFields.description = typeof rawTab?.description === 'string' ? rawTab.description : ''
  }

  tab.platformFields.douyin.productTitle = typeof rawTab?.productTitle === 'string' ? rawTab.productTitle : ''
  tab.platformFields.douyin.productLink = typeof rawTab?.productLink === 'string' ? rawTab.productLink : ''
  tab.platformFields.tencent.isDraft = Boolean(rawTab?.isDraft)
  return tab
}
```

- [ ] **Step 5: 重新跑测试，确认迁移和复制规则通过**

Run: `cd sau_frontend && node --test tests/publish-tab-state.test.js tests/publish-tab-copy.test.js`
Expected: PASS，输出新增测试通过

- [ ] **Step 6: 提交这一小步**

```bash
git add sau_frontend/src/constants/publishTabState.js sau_frontend/src/constants/publishPlatforms.js sau_frontend/src/constants/publishTabCopy.js sau_frontend/src/constants/publishDrafts.js sau_frontend/tests/publish-tab-state.test.js sau_frontend/tests/publish-tab-copy.test.js
git commit -m "feat: add unified publish tab state model"
```

## Task 2: 拆基础内容类型组件和视频号增强组件

**Files:**
- Create: `sau_frontend/src/components/publish/BaseVideoFields.vue`
- Create: `sau_frontend/src/components/publish/BaseImageTextFields.vue`
- Create: `sau_frontend/src/components/publish/PlatformEnhancementHost.vue`
- Create: `sau_frontend/src/components/publish/TencentVideoEnhancement.vue`
- Create: `sau_frontend/src/components/publish/TencentImageTextEnhancement.vue`
- Modify: `sau_frontend/src/components/BilibiliPublishFields.vue`
- Modify: `sau_frontend/src/views/PublishCenter.vue`

- [ ] **Step 1: 先写失败测试，锁定视频号增强组件在不同内容类型下的显示**

```js
import test from 'node:test'
import assert from 'node:assert/strict'

import { getPublishPlatformEnhancementComponentName } from '../src/constants/publishTabState.js'

test('视频号视频应挂载 TencentVideoEnhancement', () => {
  assert.equal(getPublishPlatformEnhancementComponentName(2, 'video'), 'TencentVideoEnhancement')
})

test('视频号图文应挂载 TencentImageTextEnhancement', () => {
  assert.equal(getPublishPlatformEnhancementComponentName(2, 'image_text'), 'TencentImageTextEnhancement')
})
```

- [ ] **Step 2: 运行测试，确认组件选择器尚未定义**

Run: `cd sau_frontend && node --test tests/publish-tab-state.test.js`
Expected: FAIL，报 `getPublishPlatformEnhancementComponentName is not a function`

- [ ] **Step 3: 建立增强组件选择器和基础组件**

```js
export function getPublishPlatformEnhancementComponentName(platformKey, contentType) {
  if (platformKey === 2 && contentType === 'video') {
    return 'TencentVideoEnhancement'
  }
  if (platformKey === 2 && contentType === 'image_text') {
    return 'TencentImageTextEnhancement'
  }
  if (platformKey === 5 && contentType === 'video') {
    return 'BilibiliVideoEnhancement'
  }
  return null
}
```

```vue
<template>
  <div class="tencent-video-enhancement">
    <el-input v-model="model.shortTitle" placeholder="请输入短标题" />
    <el-input v-model="model.collectionName" placeholder="请输入合集名称" />
    <el-checkbox v-model="model.declareOriginal" label="声明原创" />
    <el-input v-model="model.originalType" placeholder="请输入原创类型" />
    <el-input v-model="model.contentDeclaration" placeholder="请输入内容声明" />
    <el-checkbox v-model="model.isDraft" label="仅保存草稿(用手机发布)" />
  </div>
</template>
```

- [ ] **Step 4: 在 `PublishCenter.vue` 中接入基础层与增强层装配**

```vue
<BaseVideoFields
  v-if="tab.contentType === 'video'"
  v-model:title="tab.baseFields.title"
  v-model:description="tab.baseFields.description"
  v-model:topics="tab.baseFields.topics"
  v-model:schedule-enabled="tab.baseFields.scheduleEnabled"
  v-model:videos-per-day="tab.baseFields.videosPerDay"
  v-model:daily-times="tab.baseFields.dailyTimes"
  v-model:start-days="tab.baseFields.startDays"
/>

<BaseImageTextFields
  v-else
  v-model:title="tab.baseFields.title"
  v-model:note-content="tab.baseFields.noteContent"
  v-model:topics="tab.baseFields.topics"
  v-model:schedule-enabled="tab.baseFields.scheduleEnabled"
  v-model:videos-per-day="tab.baseFields.videosPerDay"
  v-model:daily-times="tab.baseFields.dailyTimes"
  v-model:start-days="tab.baseFields.startDays"
/>

<PlatformEnhancementHost
  :platform-key="tab.selectedPlatform"
  :content-type="tab.contentType"
  :platform-fields="tab.platformFields"
/>
```

- [ ] **Step 5: 手工跑前端测试，确认旧复制测试和新装配选择测试都通过**

Run: `cd sau_frontend && node --test tests/publish-tab-state.test.js tests/publish-tab-copy.test.js`
Expected: PASS

- [ ] **Step 6: 提交这一小步**

```bash
git add sau_frontend/src/components/publish/BaseVideoFields.vue sau_frontend/src/components/publish/BaseImageTextFields.vue sau_frontend/src/components/publish/PlatformEnhancementHost.vue sau_frontend/src/components/publish/TencentVideoEnhancement.vue sau_frontend/src/components/publish/TencentImageTextEnhancement.vue sau_frontend/src/components/BilibiliPublishFields.vue sau_frontend/src/views/PublishCenter.vue
git commit -m "feat: split publish center base and tencent enhancement fields"
```

## Task 3: 建立新 payload 映射并接入历史 `/postVideo`

**Files:**
- Create: `sau_frontend/src/constants/publishPayload.js`
- Create: `sau_frontend/tests/publish-payload.test.js`
- Modify: `sau_frontend/src/views/PublishCenter.vue`
- Modify: `myUtils/web_publish.py`
- Modify: `tests/test_publish_endpoints.py`

- [ ] **Step 1: 先写失败测试，锁定视频号 payload 必须带 `baseFields` 与 `platformFields.tencent`**

```js
import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPublishPayloadFromState } from '../src/constants/publishPayload.js'
import { createDefaultPublishTabState } from '../src/constants/publishTabState.js'

test('视频号图文 payload 应透传 tencent 平台增强字段', () => {
  const tab = createDefaultPublishTabState()
  tab.selectedPlatform = 2
  tab.contentType = 'image_text'
  tab.baseFields.title = '图文标题'
  tab.baseFields.noteContent = '图文正文'
  tab.platformFields.tencent.collectionName = '旅行合集'
  const payload = buildPublishPayloadFromState(tab, [])

  assert.equal(payload.type, 2)
  assert.equal(payload.contentType, 'image_text')
  assert.equal(payload.platformFields.tencent.collectionName, '旅行合集')
})
```

- [ ] **Step 2: 运行测试，确认映射文件尚未建立**

Run: `cd sau_frontend && node --test tests/publish-payload.test.js`
Expected: FAIL，报 `Cannot find module '../src/constants/publishPayload.js'`

- [ ] **Step 3: 写前端映射函数**

```js
export function buildPublishPayloadFromState(tab, accounts) {
  return {
    type: tab.selectedPlatform,
    contentType: tab.contentType,
    baseFields: {
      title: tab.baseFields.title.trim(),
      description: tab.baseFields.description.trim(),
      noteContent: tab.baseFields.noteContent.trim(),
      tags: tab.baseFields.topics,
      enableTimer: tab.baseFields.scheduleEnabled ? 1 : 0,
      videosPerDay: tab.baseFields.videosPerDay,
      dailyTimes: tab.baseFields.dailyTimes,
      startDays: tab.baseFields.startDays
    },
    platformFields: {
      tencent: tab.platformFields.tencent,
      bilibili: tab.platformFields.bilibili,
      douyin: tab.platformFields.douyin,
      kuaishou: tab.platformFields.kuaishou,
      xiaohongshu: tab.platformFields.xiaohongshu
    },
    fileList: tab.materials.fileList.map((file) => file.path),
    accountList: tab.accounts.selectedAccountIds.map((accountId) => {
      const account = accounts.find((item) => item.id === accountId)
      return account ? account.filePath : accountId
    })
  }
}
```

- [ ] **Step 4: 更新 `myUtils/web_publish.py` 解析逻辑，兼容旧平铺结构并优先消费新结构**

```python
base_fields = request_payload.get("baseFields")
platform_fields = request_payload.get("platformFields")

if isinstance(base_fields, dict):
    title = _get_string(base_fields, "title")
    description = _get_string(base_fields, "description")
    note_content = _get_string(base_fields, "noteContent")
    tags = _get_string_tuple(base_fields, "tags")
else:
    title = _get_string(request_payload, "title")
    description = _get_string(request_payload, "description")
    note_content = _get_string(request_payload, "noteContent")
    tags = _get_string_tuple(request_payload, "tags")
```

- [ ] **Step 5: 补 Python 接口测试，锁定视频号图文增强字段请求不会被拒绝**

```python
def test_post_video_accepts_tencent_image_text_with_platform_fields(self):
    payload = {
        "type": 2,
        "contentType": "image_text",
        "baseFields": {
            "title": "图文标题",
            "description": "",
            "noteContent": "图文正文",
            "tags": ["旅行"],
            "enableTimer": 1,
            "videosPerDay": 1,
            "dailyTimes": ["10:00"],
            "startDays": 0,
        },
        "platformFields": {
            "tencent": {
                "collectionName": "旅行合集",
                "declareOriginal": True,
            }
        },
        "fileList": ["image-1.png", "image-2.png"],
        "accountList": ["tencent_creator.json"],
    }
```

- [ ] **Step 6: 跑前端映射测试和 Python 接口测试**

Run: `cd sau_frontend && node --test tests/publish-payload.test.js`
Expected: PASS

Run: `python -m unittest tests.test_publish_endpoints`
Expected: PASS

- [ ] **Step 7: 提交这一小步**

```bash
git add sau_frontend/src/constants/publishPayload.js sau_frontend/tests/publish-payload.test.js sau_frontend/src/views/PublishCenter.vue myUtils/web_publish.py tests/test_publish_endpoints.py
git commit -m "feat: map unified publish payload through legacy endpoint"
```

## Task 4: 补视频号增强字段的 bridge / CLI 透传

**Files:**
- Modify: `sau_bridge/publish.py`
- Modify: `tests/test_sau_bridge_publish.py`
- Modify: `sau_cli.py`
- Modify: `tests/test_sau_browser_cli.py`

- [ ] **Step 1: 先写失败测试，锁定视频号视频与图文请求对象包含增强字段**

```python
def test_run_publish_note_parses_tencent_enhancement_fields():
    payload = {
        "platform": "tencent",
        "account_name": "creator",
        "image_files": ["1.png", "2.png"],
        "title": "图文标题",
        "note": "图文正文",
        "tags": ["旅行"],
        "schedule": "2026-06-09 10:00",
        "collection_name": "旅行合集",
        "declare_original": True,
        "original_type": "生活",
        "content_declaration": "无需声明",
        "is_draft": True,
    }
```

- [ ] **Step 2: 运行测试，确认 bridge/CLI 还未消费这些字段**

Run: `python -m unittest tests.test_sau_bridge_publish tests.test_sau_browser_cli`
Expected: FAIL，断言字段不存在或未透传

- [ ] **Step 3: 为 `sau_bridge.publish` 增加视频号增强字段载体**

```python
@dataclass(frozen=True, slots=True)
class PublishNotePayload:
    platform: str
    account_name: str
    image_files: list[Path]
    title: str
    note: str
    tags: list[str]
    schedule: str | None = None
    collection_name: str = ""
    declare_original: bool = False
    original_type: str = ""
    content_declaration: str = ""
    is_draft: bool = False
```

- [ ] **Step 4: 扩展 `sau_cli.py` 的请求对象与分发代码**

```python
@dataclass(slots=True)
class TencentNoteUploadRequest:
    account_name: str
    image_files: list[Path]
    title: str
    note: str
    tags: list[str]
    publish_date: datetime | int
    short_title: str | None = None
    collection_name: str = ""
    declare_original: bool = False
    original_type: str = ""
    content_declaration: str = ""
    is_draft: bool = False
    publish_strategy: str = TENCENT_PUBLISH_STRATEGY_IMMEDIATE
    debug: bool = True
    headless: bool = True
```

- [ ] **Step 5: 跑 bridge / CLI 测试确认透传通过**

Run: `python -m unittest tests.test_sau_bridge_publish tests.test_sau_browser_cli`
Expected: PASS

- [ ] **Step 6: 提交这一小步**

```bash
git add sau_bridge/publish.py tests/test_sau_bridge_publish.py sau_cli.py tests/test_sau_browser_cli.py
git commit -m "feat: pass tencent enhancement fields through bridge and cli"
```

## Task 5: 接通视频号图文 uploader 链路

**Files:**
- Modify: `uploader/tencent_uploader/main.py`
- Create: `tests/test_tencent_note_publish.py`

- [ ] **Step 1: 先写失败测试，锁定 `TencentNote` 会按顺序执行“切模式 -> 传图 -> 填标题/话题 -> 定时/发布”**

```python
import unittest
from unittest.mock import AsyncMock, patch

from uploader.tencent_uploader.main import TencentNote


class TencentNotePublishTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_note_content_calls_mode_switch_upload_and_fill(self):
        app = TencentNote(
            image_paths=["1.png", "2.png"],
            title="图文标题",
            note="图文正文",
            tags=["旅行"],
            publish_date=0,
            account_file="cookies/tencent.json",
        )
        page = object()
        with patch.object(app, "switch_to_note_mode", new=AsyncMock()) as mock_switch, patch.object(
            app, "upload_note_images", new=AsyncMock()
        ) as mock_upload, patch.object(app, "fill_note_title_and_tags", new=AsyncMock()) as mock_fill:
            await app.upload_note_content(page)

        mock_switch.assert_awaited_once_with(page)
        mock_upload.assert_awaited_once_with(page)
        mock_fill.assert_awaited_once_with(page)
```

- [ ] **Step 2: 运行测试，确认 `TencentNote` 仍然是 `NotImplementedError` 空壳**

Run: `python -m unittest tests.test_tencent_note_publish`
Expected: FAIL，报方法未实现或断言未调用

- [ ] **Step 3: 实现 `switch_to_note_mode`、`upload_note_images`、`fill_note_title_and_tags` 的最小可用版本**

```python
async def switch_to_note_mode(self, page: Page) -> None:
    note_tab = page.locator('text="图文"').first
    if await note_tab.count():
        await note_tab.click()
        await page.wait_for_timeout(1000)
        return
    note_entry = page.locator('text="发布图文"').first
    if await note_entry.count():
        await note_entry.click()
        await page.wait_for_timeout(1000)
        return
    raise RuntimeError("未找到视频号图文发布入口")

async def upload_note_images(self, page: Page) -> None:
    file_input = page.locator('input[type="file"]').first
    await file_input.set_input_files(self.image_paths)
    await page.wait_for_timeout(1000)

async def fill_note_title_and_tags(self, page: Page) -> None:
    await page.locator("div.input-editor").click()
    await page.keyboard.type(self.title)
    await page.keyboard.press("Enter")
    for tag in self.tags:
        await page.keyboard.type(f"#{tag}")
        await page.keyboard.press("Space")
```

- [ ] **Step 4: 接上图文专属增强字段**

```python
async def fill_note_body(self, page: Page) -> None:
    if not self.note:
        return
    await page.keyboard.press("Enter")
    await page.keyboard.type(self.note)
```

```python
async def prepare_note_for_publish(self, page: Page) -> None:
    await self.fill_note_title_and_tags(page)
    await self.fill_note_body(page)
    await self.apply_collection(page)
    if self.declare_original:
        await self.apply_original_statement(page)
```

- [ ] **Step 5: 跑 `TencentNote` 测试，至少锁住执行顺序与非空实现**

Run: `python -m unittest tests.test_tencent_note_publish`
Expected: PASS

- [ ] **Step 6: 提交这一小步**

```bash
git add uploader/tencent_uploader/main.py tests/test_tencent_note_publish.py
git commit -m "feat: implement tencent note publish flow"
```

## Task 6: 整体验证视频号首阶段链路

**Files:**
- Modify: `docs/superpowers/specs/2026-06-08-publish-center-platform-fields-design.md`
  - 若实现中有与 spec 不一致的字段，回写决策

- [ ] **Step 1: 跑前端状态与 payload 测试**

Run: `cd sau_frontend && node --test tests/publish-tab-state.test.js tests/publish-tab-copy.test.js tests/publish-payload.test.js`
Expected: PASS

- [ ] **Step 2: 跑 Python 发布接口与 bridge/CLI 测试**

Run: `python -m unittest tests.test_publish_endpoints tests.test_sau_bridge_publish tests.test_sau_browser_cli`
Expected: PASS

- [ ] **Step 3: 跑视频号图文 uploader 单测**

Run: `python -m unittest tests.test_tencent_note_publish`
Expected: PASS

- [ ] **Step 4: 手工验收本地链路**

Run:

```bash
python sau_backend.py
cd sau_frontend && npm run dev
```

Expected:

- 发布中心能看到视频号视频增强组件
- 切到图文时能看到视频号图文增强组件
- 提交请求 payload 中包含 `baseFields` 和 `platformFields.tencent`

- [ ] **Step 5: 若字段实际页面与 spec 不一致，回写 spec**

```md
- 视频号图文页面未发现稳定的短标题控件，因此首阶段不展示 `shortTitle`
- 视频号图文页面未发现稳定的图文封面控件，因此首阶段不展示 `noteCoverPath`
```

- [ ] **Step 6: 提交这一小步**

```bash
git add sau_frontend tests myUtils sau_bridge sau_cli.py uploader/tencent_uploader/main.py docs/superpowers/specs/2026-06-08-publish-center-platform-fields-design.md
git commit -m "feat: complete tencent publish center phase one"
```

## 自检

### Spec 覆盖

- 统一字段模型：Task 1
- 基础组件 + 平台增强组件：Task 2
- 历史 Web 接口映射：Task 3
- bridge / CLI 透传：Task 4
- `TencentNote` 实现：Task 5
- 验证与 spec 回写：Task 6

### 占位扫描

- 计划中没有 `TODO/TBD/后续补` 类占位步骤。
- 每个任务都包含失败测试、运行命令、最小实现、再次验证和提交步骤。

### 类型一致性

- 前端统一使用 `baseFields` / `platformFields.tencent`
- 后端统一使用 `baseFields` / `platformFields`
- 视频号图文请求对象统一命名为 `TencentNoteUploadRequest`

