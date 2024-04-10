import subprocess

if __name__ == '__main__':
    exe_file = "/Users/admin/libs/Juggle/juggle.app/Contents/MacOS/roller_ball"
    process = subprocess.Popen(exe_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        stdout, stderr = process.communicate()
        print(stdout.decode())