import unittest

from myUtils.douyin_metrics import extract_douyin_metrics_from_text, parse_douyin_metric_value


class DouyinMetricsParsingTests(unittest.TestCase):
    """验证抖音运营数据文本解析规则，避免页面文案微调时把数值抓错。"""

    def test_parse_douyin_metric_value_supports_units(self):
        """解析器应支持纯数字、万、亿和空占位符。"""

        self.assertEqual(parse_douyin_metric_value("123"), 123)
        self.assertEqual(parse_douyin_metric_value("1.2万"), 12000)
        self.assertEqual(parse_douyin_metric_value("3亿"), 300000000)
        self.assertIsNone(parse_douyin_metric_value("--"))

    def test_extract_douyin_metrics_from_text_maps_known_labels(self):
        """文本解析应把抖音首页常见指标标签映射到统一字段。"""

        metrics = extract_douyin_metrics_from_text(
            """
            粉丝数 1.2万
            获赞 3.4万
            作品数 56
            关注 78
            播放量 9.1万
            """
        )

        self.assertEqual(metrics.follower_count, 12000)
        self.assertEqual(metrics.like_count, 34000)
        self.assertEqual(metrics.work_count, 56)
        self.assertEqual(metrics.following_count, 78)
        self.assertEqual(metrics.total_view_count, 91000)
        self.assertEqual(metrics.raw_metrics["粉丝数"], 12000)


if __name__ == "__main__":
    unittest.main()
