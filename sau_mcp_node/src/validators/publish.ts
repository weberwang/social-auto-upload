import { z } from "zod";

import { accountNameSchema, platformSchema } from "./account.js";

/**
 * 发布目标。
 * 当前按平台 + 账号展开父任务。
 */
export const publishTargetSchema = z.object({
  platform: platformSchema,
  account_name: accountNameSchema,
});

/**
 * 素材单元。
 * 视频和图文共用一套联合类型，图文多图按单个素材单元处理。
 */
export const materialSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("video"),
    file_path: z.string().min(1),
  }),
  z.object({
    type: z.literal("image_text"),
    files: z.array(z.string().min(1)).min(1),
  }),
]);

/**
 * 发布元数据。
 * 先约束当前 bridge 真正会消费的字段。
 */
const publishMetadataBaseSchema = z.object({
  title: z.string().min(1),
  desc: z.string().optional(),
  note: z.string().optional(),
  tags: z.array(z.string()).default([]),
  tid: z.number().int().positive().optional(),
});

type PublishMetadataInput = z.infer<typeof publishMetadataBaseSchema>;

export const publishMetadataSchema = publishMetadataBaseSchema.superRefine((value: PublishMetadataInput, context: z.RefinementCtx) => {
  if (!value.desc && !value.note) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      message: "metadata must include desc or note",
    });
  }
});

/**
 * 发布请求输入。
 * Task 6 先支持 immediate 模式。
 */
const publishSubmitBaseSchema = z.object({
  trigger_mode: z.literal("immediate"),
  content_type: z.enum(["video", "image_text"]),
  targets: z.array(publishTargetSchema).min(1),
  materials: z.array(materialSchema).min(1),
  metadata: publishMetadataSchema,
});

type PublishSubmitBaseInput = z.infer<typeof publishSubmitBaseSchema>;

export const publishSubmitSchema = publishSubmitBaseSchema.superRefine((value: PublishSubmitBaseInput, context: z.RefinementCtx) => {
  const materialTypeSet = new Set(value.materials.map((material: z.infer<typeof materialSchema>) => material.type));
  if (materialTypeSet.size !== 1 || !materialTypeSet.has(value.content_type)) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      message: "materials must match content_type",
    });
  }
  if (
    value.content_type === "video" &&
    value.targets.some((target: z.infer<typeof publishTargetSchema>) => target.platform === "bilibili") &&
    value.metadata.tid == null
  ) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      message: "metadata.tid is required for bilibili video publish",
    });
  }
  if (value.content_type === "video" && value.metadata.desc == null) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      message: "metadata.desc is required for video publish",
    });
  }
  if (value.content_type === "image_text" && value.metadata.note == null) {
    context.addIssue({
      code: z.ZodIssueCode.custom,
      message: "metadata.note is required for image_text publish",
    });
  }
});

export type PublishSubmitInput = z.infer<typeof publishSubmitSchema>;
