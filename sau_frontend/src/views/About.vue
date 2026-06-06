<template>
  <div class="about">
    <el-card class="about-card">
      <div class="about-header">
        <h1>自媒体自动化运营系统</h1>
        <p class="version">social-auto-upload</p>
      </div>

      <el-divider />

      <div class="about-section">
        <h3>系统简介</h3>
        <p>
          本系统是一款强大的自动化工具，帮助内容创作者和运营人员一键将视频内容高效发布到多个国内外主流社交媒体平台。
          当前主线已覆盖视频上传、部分平台图文发布、批量发布与定时发布等能力。
        </p>
      </div>

      <div class="about-section">
        <h3>支持平台</h3>
        <el-table :data="platformRows" size="small" border>
          <el-table-column prop="name" label="平台" width="120" />
          <el-table-column label="支持素材" width="220">
            <template #default="scope">
              <div class="material-tags">
                <el-tag
                  v-for="materialType in scope.row.supportedMaterialTypes"
                  :key="materialType"
                  size="small"
                  effect="plain"
                >
                  {{ materialType }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="materialSupportDescription" label="说明" />
        </el-table>
      </div>

      <div class="about-section">
        <h3>核心功能</h3>
        <ul class="feature-list">
          <li>多平台账号管理与登录状态维护</li>
          <li>视频、图片素材上传与管理</li>
          <li>一键多平台发布</li>
          <li>定时发布与批量发布</li>
          <li>Cookie 导入导出</li>
        </ul>
      </div>

      <div class="about-section">
        <h3>技术栈</h3>
        <div class="tech-tags">
          <el-tag effect="plain">Vue 3</el-tag>
          <el-tag effect="plain">Element Plus</el-tag>
          <el-tag effect="plain">Pinia</el-tag>
          <el-tag effect="plain">Flask</el-tag>
          <el-tag effect="plain">Playwright</el-tag>
          <el-tag effect="plain">SQLite</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { PUBLISH_PLATFORM_OPTIONS } from '@/constants/publishPlatforms'

/**
 * 关于页直接复用发布平台配置，避免平台能力说明和实际支持矩阵出现两份口径。
 */
const platformRows = computed(() => PUBLISH_PLATFORM_OPTIONS)
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.about {
  max-width: 700px;
  margin: 0 auto;

  .about-card {
    .about-header {
      text-align: center;

      h1 {
        color: $text-primary;
        margin: 0 0 8px 0;
        font-size: 24px;
      }

      .version {
        color: $text-secondary;
        font-size: 14px;
        margin: 0;
      }
    }

    .about-section {
      margin-bottom: 24px;

      h3 {
        font-size: 16px;
        color: $text-primary;
        margin: 0 0 12px 0;
      }

      p {
        color: $text-secondary;
        line-height: 1.8;
        margin: 0;
      }

      .platform-tags,
      .tech-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .material-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .feature-list {
        margin: 0;
        padding-left: 20px;
        color: $text-secondary;
        line-height: 2;
      }
    }
  }
}
</style>
