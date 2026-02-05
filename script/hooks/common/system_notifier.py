"""系统通知模块 - 使用 osascript 发送 macOS 系统通知."""
import subprocess


def send_notification(title: str, message: str) -> bool:
    """
    使用 AppleScript 发送系统通知.

    Args:
        title: 通知标题
        message: 通知内容

    Returns:
        bool: 是否发送成功
    """
    # 转义特殊字符，防止 AppleScript 注入
    escaped_title = title.replace('"', '\\"').replace("'", "\\'")
    escaped_message = message.replace('"', '\\"').replace("'", "\\'")

    script = f'display notification "{escaped_message}" with title "{escaped_title}"'

    try:
        subprocess.run(
            ['osascript', '-e', script],
            check=True,
            timeout=5,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.TimeoutExpired:
        return False
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False
