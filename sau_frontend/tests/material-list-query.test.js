import test from 'node:test'
import assert from 'node:assert/strict'

import {
  MATERIAL_PAGE_SIZE_OPTIONS,
  MATERIAL_SORT_OPTIONS,
  MATERIAL_TYPE_FILTER_OPTIONS,
  buildMaterialListQueryParams
} from '../src/composables/materialListQuery.js'

test('素材分页查询参数应映射到后端分页接口约定', () => {
  const result = buildMaterialListQueryParams({
    currentPage: 3,
    pageSize: 50,
    searchKeyword: 'cover',
    selectedType: '图片',
    selectedSort: 'size_asc'
  })

  assert.deepEqual(result, {
    page: 3,
    page_size: 50,
    keyword: 'cover',
    material_type: '图片',
    sort_by: 'filesize',
    sort_order: 'asc'
  })
})

test('素材分页查询参数默认应使用最新上传和全部类型', () => {
  const result = buildMaterialListQueryParams({
    currentPage: 1,
    pageSize: 20,
    searchKeyword: '  '
  })

  assert.deepEqual(result, {
    page: 1,
    page_size: 20,
    keyword: '',
    material_type: MATERIAL_TYPE_FILTER_OPTIONS[0].value,
    sort_by: 'upload_time',
    sort_order: 'desc'
  })
  assert.equal(MATERIAL_SORT_OPTIONS[0].value, 'date_desc')
  assert.deepEqual(MATERIAL_PAGE_SIZE_OPTIONS, [10, 20, 50, 100])
})
