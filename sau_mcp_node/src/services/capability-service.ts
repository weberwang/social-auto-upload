import { buildCapabilityMatrix } from "../shared/platforms.js";

/**
 * MCP 能力矩阵服务。
 * 当前先聚合平台、平台详情和工具列表，后续再补更多查询维度。
 */
export class CapabilityService {
  /**
   * 返回 Node MCP 当前对外暴露的能力矩阵。
   */
  public getCapabilities(): {
    tools: string[];
    platforms: string[];
    legacy_platforms: string[];
    platform_details: Record<string, { displayName: string; supportedMaterialTypes: string[] }>;
  } {
    const matrix = buildCapabilityMatrix();
    return {
      tools: [
        "account_login",
        "account_check",
        "publish_submit",
        "draft_save",
        "draft_delete",
        "schedule_create",
        "schedule_update",
        "schedule_delete",
        "task_cancel",
        "task_retry",
      ],
      platforms: matrix.platforms,
      legacy_platforms: matrix.legacyPlatforms,
      platform_details: matrix.platformDetails,
    };
  }
}
