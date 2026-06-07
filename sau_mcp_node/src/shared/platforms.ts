/**
 * 主线平台名称。
 * 这里统一承载 Node MCP 会直接对外暴露的平台清单。
 */
export type PlatformName =
  | "douyin"
  | "kuaishou"
  | "xiaohongshu"
  | "bilibili"
  | "tencent";

/**
 * 平台素材能力明细。
 * 后续 `capabilities` 路由会直接复用这个结构对外返回。
 */
export type PlatformDetail = {
  displayName: string;
  supportedMaterialTypes: Array<"video" | "image_text">;
};

/**
 * 兼容历史前端/旧 Web 的平台编号映射。
 * 这层映射先固定下来，避免后续 Node MCP 接入时重新发散。
 */
export const LEGACY_PLATFORM_ID_MAP: Record<number, PlatformName> = {
  1: "xiaohongshu",
  2: "tencent",
  3: "douyin",
  4: "kuaishou",
  5: "bilibili",
};

/**
 * 构建 MCP 能力矩阵。
 * `legacyPlatforms` 保留旧 MCP 协议顺序，`platforms` 表示新的完整主线能力面。
 */
export function buildCapabilityMatrix(): {
  legacyPlatforms: PlatformName[];
  platforms: PlatformName[];
  platformDetails: Record<PlatformName, PlatformDetail>;
} {
  return {
    legacyPlatforms: ["douyin", "kuaishou", "xiaohongshu", "bilibili"],
    platforms: ["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent"],
    platformDetails: {
      douyin: {
        displayName: "抖音",
        supportedMaterialTypes: ["video", "image_text"],
      },
      kuaishou: {
        displayName: "快手",
        supportedMaterialTypes: ["video", "image_text"],
      },
      xiaohongshu: {
        displayName: "小红书",
        supportedMaterialTypes: ["video", "image_text"],
      },
      bilibili: {
        displayName: "B站",
        supportedMaterialTypes: ["video"],
      },
      tencent: {
        displayName: "视频号",
        supportedMaterialTypes: ["video", "image_text"],
      },
    },
  };
}
