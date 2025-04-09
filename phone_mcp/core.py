import asyncio
import subprocess
from .config import COMMAND_TIMEOUT, AUTO_RETRY_CONNECTION, MAX_RETRY_COUNT

async def run_command(cmd: str, timeout: int = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output.

    Args:
        cmd (str): Shell command to execute.
        timeout (int, optional): Command execution timeout in seconds.
                                If None, uses the default from config.

    Returns:
        tuple[bool, str]: A tuple containing:
            - bool: True if command succeeded (exit code 0), False otherwise
            - str: Command output (stdout) if successful, error message (stderr) if failed
    """
    # Use default timeout from config if not specified
    if timeout is None:
        timeout = COMMAND_TIMEOUT
        
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode == 0:
                return True, stdout.decode('utf-8')
            else:
                return False, stderr.decode('utf-8')
        except asyncio.TimeoutError:
            # Try to terminate the process if it timed out
            try:
                process.terminate()
                await process.wait()
            except:
                pass
            return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, str(e)


async def check_device_connection(mcp=None) -> str:
    """Check if an Android device is connected via ADB.

    Verifies that an Android device is properly connected and recognized
    by ADB, which is required for all other functions to work.

    Args:
        mcp: MCP instance (optional, can be None when called from CLI)

    Returns:
        str: Status message indicating whether a device is connected and
             ready, or an error message if no device is found.
    """
    retry_count = 0
    while True:
        success, output = await run_command("adb devices")

        if success:
            if "device" in output and not output.strip().endswith("devices"):
                return "Device is connected and ready."
            else:
                if AUTO_RETRY_CONNECTION and retry_count < MAX_RETRY_COUNT:
                    # Try restarting ADB server
                    if retry_count == 0:
                        await run_command("adb kill-server")
                        await asyncio.sleep(1)
                        await run_command("adb start-server")
                        await asyncio.sleep(2)
                    retry_count += 1
                    continue
                return "No device found. Please connect a device and ensure USB debugging is enabled."
        else:
            return f"Failed to check device connection: {output}"
        
        # If we're not retrying, break out of the loop
        break 