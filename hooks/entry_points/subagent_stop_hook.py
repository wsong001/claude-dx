#!/usr/bin/env python3
"""SubagentStop Hook入口脚本."""
import sys
import json
from pathlib import Path

# 添加hooks目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from handlers.subagent_stop import SubagentStopHandler
from common.logger import logger


def main():
    """主函数."""
    try:
        # 1. 读取stdin JSON
        input_data = json.load(sys.stdin)

        # 2. 创建处理器并处理
        handler = SubagentStopHandler()
        handler.process(input_data)

        # 3. 输出原始JSON到stdout(pass-through)
        json.dump(input_data, sys.stdout)
        sys.stdout.flush()

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        print("{}", flush=True)

    except Exception as e:
        logger.error(f"Hook error: {e}", exc_info=e)
        try:
            sys.stdin.seek(0)
            sys.stdout.write(sys.stdin.read())
            sys.stdout.flush()
        except Exception:
            print("{}", flush=True)

    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
