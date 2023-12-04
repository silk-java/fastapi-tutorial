from loguru import logger
import os

# 日志文件的存储路径
log_path = './logs'

if not os.path.exists(log_path):
    os.makedirs(log_path)

# 配置日志
logger.add(
    os.path.join(log_path, "{time:YYYY-MM-DD}.log"),  # 日志文件路径，每天一个新文件
    rotation="1 MB",  # 文件达到10MB时创建新的日志文件
    retention="30 days",  # 保留最新30天的日志文件
    # compression="zip",  # 压缩历史日志文件
    level="INFO"  # 日志级别
)