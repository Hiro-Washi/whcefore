#統計情報を取得する
import subprocess

def get_icn_statistics():
    try:
        result = subprocess.run(["cefstatus"], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error retrieving statistics: {e}")

if __name__ == "__main__":
    get_icn_statistics()

