/**
 * B站分区选项。
 * 这里对齐后端 `VideoZoneTypes` 的 tid，前端展示中文名称，提交时仍直接传接口需要的数值。
 * 历史枚举里 `VLOG` 与 `Mugen` 共用 `tid=19`，这里先保留游戏分组中的 `Mugen`，避免下拉出现同 value 冲突。
 */
export const BILIBILI_CATEGORY_GROUPS = [
  {
    label: '番剧',
    options: [
      { label: '番剧', value: 13 },
      { label: '连载中番剧', value: 33 },
      { label: '已完结番剧', value: 32 },
      { label: '资讯', value: 51 },
      { label: '官方延伸', value: 152 }
    ]
  },
  {
    label: '电影',
    options: [
      { label: '电影', value: 23 }
    ]
  },
  {
    label: '国创',
    options: [
      { label: '国创', value: 167 },
      { label: '国产动画', value: 153 },
      { label: '国产原创相关', value: 168 },
      { label: '布袋戏', value: 169 },
      { label: '动态漫·广播剧', value: 195 },
      { label: '资讯', value: 170 }
    ]
  },
  {
    label: '电视剧',
    options: [
      { label: '电视剧', value: 11 }
    ]
  },
  {
    label: '纪录片',
    options: [
      { label: '纪录片', value: 177 }
    ]
  },
  {
    label: '动画',
    options: [
      { label: '动画', value: 1 },
      { label: 'MAD·AMV', value: 24 },
      { label: 'MMD·3D', value: 25 },
      { label: '短片·手书·配音', value: 47 },
      { label: '手办·模玩', value: 210 },
      { label: '特摄', value: 86 },
      { label: '动漫杂谈', value: 253 },
      { label: '综合', value: 27 }
    ]
  },
  {
    label: '游戏',
    options: [
      { label: '游戏', value: 4 },
      { label: '单机游戏', value: 17 },
      { label: '电子竞技', value: 171 },
      { label: '手机游戏', value: 172 },
      { label: '网络游戏', value: 65 },
      { label: '桌游棋牌', value: 173 },
      { label: 'GMV', value: 121 },
      { label: '音游', value: 136 },
      { label: 'Mugen', value: 19 }
    ]
  },
  {
    label: '鬼畜',
    options: [
      { label: '鬼畜', value: 119 },
      { label: '鬼畜调教', value: 22 },
      { label: '音MAD', value: 26 },
      { label: '人力VOCALOID', value: 126 },
      { label: '鬼畜剧场', value: 216 },
      { label: '教程演示', value: 127 }
    ]
  },
  {
    label: '音乐',
    options: [
      { label: '音乐', value: 3 },
      { label: '原创音乐', value: 28 },
      { label: '翻唱', value: 31 },
      { label: '演奏', value: 59 },
      { label: 'VOCALOID·UTAU', value: 30 },
      { label: '音乐现场', value: 29 },
      { label: 'MV', value: 193 },
      { label: '乐评盘点', value: 243 },
      { label: '音乐教学', value: 244 },
      { label: '音乐综合', value: 130 }
    ]
  },
  {
    label: '舞蹈',
    options: [
      { label: '舞蹈', value: 129 },
      { label: '宅舞', value: 20 },
      { label: '街舞', value: 198 },
      { label: '明星舞蹈', value: 199 },
      { label: '中国舞', value: 200 },
      { label: '舞蹈综合', value: 154 },
      { label: '舞蹈教程', value: 156 }
    ]
  },
  {
    label: '影视',
    options: [
      { label: '影视', value: 181 },
      { label: '影视杂谈', value: 182 },
      { label: '影视剪辑', value: 183 },
      { label: '小剧场', value: 85 },
      { label: '预告·资讯', value: 184 }
    ]
  },
  {
    label: '娱乐',
    options: [
      { label: '娱乐', value: 5 },
      { label: '综艺', value: 71 },
      { label: '娱乐杂谈', value: 241 },
      { label: '粉丝创作', value: 242 },
      { label: '明星综合', value: 137 }
    ]
  },
  {
    label: '知识',
    options: [
      { label: '知识', value: 36 },
      { label: '科学科普', value: 201 },
      { label: '社科·法律·心理', value: 124 },
      { label: '人文历史', value: 228 },
      { label: '财经商业', value: 207 },
      { label: '校园学习', value: 208 },
      { label: '职业职场', value: 209 },
      { label: '设计·创意', value: 229 },
      { label: '野生技能协会', value: 122 }
    ]
  },
  {
    label: '科技',
    options: [
      { label: '科技', value: 188 },
      { label: '数码', value: 95 },
      { label: '软件应用', value: 230 },
      { label: '计算机技术', value: 231 },
      { label: '科工机械', value: 232 }
    ]
  },
  {
    label: '资讯',
    options: [
      { label: '资讯', value: 202 },
      { label: '热点', value: 203 },
      { label: '环球', value: 204 },
      { label: '社会', value: 205 },
      { label: '综合', value: 206 }
    ]
  },
  {
    label: '美食',
    options: [
      { label: '美食', value: 211 },
      { label: '美食制作', value: 76 },
      { label: '美食侦探', value: 212 },
      { label: '美食测评', value: 213 },
      { label: '田园美食', value: 214 },
      { label: '美食记录', value: 215 }
    ]
  },
  {
    label: '生活',
    options: [
      { label: '生活', value: 160 },
      { label: '搞笑', value: 138 },
      { label: '出行', value: 250 },
      { label: '三农', value: 251 },
      { label: '家居房产', value: 239 },
      { label: '手工', value: 161 },
      { label: '绘画', value: 162 },
      { label: '日常', value: 21 }
    ]
  },
  {
    label: '汽车',
    options: [
      { label: '汽车', value: 223 },
      { label: '赛车', value: 245 },
      { label: '改装玩车', value: 246 },
      { label: '新能源车', value: 247 },
      { label: '房车', value: 248 },
      { label: '摩托车', value: 240 },
      { label: '购车攻略', value: 227 },
      { label: '汽车生活', value: 176 }
    ]
  },
  {
    label: '时尚',
    options: [
      { label: '时尚', value: 155 },
      { label: '美妆护肤', value: 157 },
      { label: '仿妆cos', value: 252 },
      { label: '穿搭', value: 158 },
      { label: '时尚潮流', value: 159 }
    ]
  },
  {
    label: '运动',
    options: [
      { label: '运动', value: 234 },
      { label: '篮球', value: 235 },
      { label: '足球', value: 249 },
      { label: '健身', value: 164 },
      { label: '竞技体育', value: 236 },
      { label: '运动文化', value: 237 },
      { label: '运动综合', value: 238 }
    ]
  },
  {
    label: '动物圈',
    options: [
      { label: '动物圈', value: 217 },
      { label: '喵星人', value: 218 },
      { label: '汪星人', value: 219 },
      { label: '大熊猫', value: 220 },
      { label: '野生动物', value: 221 },
      { label: '爬宠', value: 222 },
      { label: '动物综合', value: 75 }
    ]
  }
]
