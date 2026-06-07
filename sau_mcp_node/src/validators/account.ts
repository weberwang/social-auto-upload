import { z } from "zod";

/**
 * 主线平台枚举。
 * 账号任务和发布任务都复用这一套平台白名单。
 */
export const platformSchema = z.enum(["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent"]);

/**
 * 账号名规则。
 * 直接对齐现有 Python helper 的文件名安全约束。
 */
export const accountNameSchema = z.string().regex(/^[A-Za-z0-9_-]+$/);

/**
 * 账号登录输入校验。
 */
export const accountLoginSchema = z.object({
  platform: platformSchema,
  account_name: accountNameSchema,
  headless: z.boolean().default(true),
});

/**
 * 账号校验输入校验。
 */
export const accountCheckSchema = z.object({
  platform: platformSchema,
  account_name: accountNameSchema,
});

export type AccountLoginInput = z.infer<typeof accountLoginSchema>;
export type AccountCheckInput = z.infer<typeof accountCheckSchema>;
