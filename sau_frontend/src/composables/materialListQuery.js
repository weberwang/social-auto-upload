/**
 * 素材类型筛选项。
 * 素材管理页与后端查询参数共用这一份定义，避免文案和实际筛选值漂移。
 */
export const MATERIAL_TYPE_FILTER_OPTIONS = [
  { label: '全部类型', value: 'all' },
  { label: '视频', value: '视频' },
  { label: '图片', value: '图片' },
  { label: '其他', value: '其他' }
]

/**
 * 素材排序选项。
 * value 继续保持前端可读语义，再由查询参数构造器映射到后端字段。
 */
export const MATERIAL_SORT_OPTIONS = [
  { label: '最新上传', value: 'date_desc' },
  { label: '最早上传', value: 'date_asc' },
  { label: '文件最大', value: 'size_desc' },
  { label: '文件最小', value: 'size_asc' }
]

/**
 * 素材分页大小候选项。
 */
export const MATERIAL_PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

/**
 * 把前端素材管理页状态映射为后端分页查询参数。
 * 这里统一收口字段名转换，避免组件里散落着 `sort_by`、`sort_order` 这类接口细节。
 */
export function buildMaterialListQueryParams(options) {
  const {
    currentPage,
    pageSize,
    searchKeyword = '',
    selectedType = MATERIAL_TYPE_FILTER_OPTIONS[0].value,
    selectedSort = MATERIAL_SORT_OPTIONS[0].value
  } = options

  const sortMapping = {
    date_desc: { sort_by: 'upload_time', sort_order: 'desc' },
    date_asc: { sort_by: 'upload_time', sort_order: 'asc' },
    size_desc: { sort_by: 'filesize', sort_order: 'desc' },
    size_asc: { sort_by: 'filesize', sort_order: 'asc' }
  }
  const sortParams = sortMapping[selectedSort] || sortMapping.date_desc

  return {
    page: currentPage,
    page_size: pageSize,
    keyword: searchKeyword.trim(),
    material_type: selectedType,
    sort_by: sortParams.sort_by,
    sort_order: sortParams.sort_order
  }
}
