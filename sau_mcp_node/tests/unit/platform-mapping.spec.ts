import { describe, expect, it } from "vitest";

import { buildCapabilityMatrix, LEGACY_PLATFORM_ID_MAP } from "../../src/shared/platforms.js";

describe("platform capability matrix", () => {
  it("keeps old platform order and appends tencent in the new matrix", () => {
    const matrix = buildCapabilityMatrix();

    expect(matrix.legacyPlatforms).toEqual(["douyin", "kuaishou", "xiaohongshu", "bilibili"]);
    expect(matrix.platforms).toEqual(["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent"]);
    expect(matrix.platformDetails.tencent.supportedMaterialTypes).toEqual(["video", "image_text"]);
    expect(LEGACY_PLATFORM_ID_MAP[5]).toBe("bilibili");
  });
});
