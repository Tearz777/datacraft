import readline
import os

from core.ui import box, path_completer
from core.modes.power import run_power_mode
from core.modes.basic import run_basic_mode


if __name__ == "__main__":
    readline.set_completer(path_completer)
    readline.set_completer_delims('\t\n')
    readline.parse_and_bind('tab: complete')

    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("DataCraft v2.5")

        while True:
            print("\nPilih mode:")
            print("[1] Power User")
            print("[2] Basic")
            print("[0] Keluar")

            mode = input("Pilih: ").strip()

            if mode == "1":
                run_power_mode()
            elif mode == "2":
                run_basic_mode()
            elif mode == "0":
                os.system('cls' if os.name == 'nt' else 'clear')
                box("👋 Sampai jumpa!")
                box("Created By : Thery Vissabil Lillah")
                box("Android Termux")
                break
            else:
                print("❌ Pilihan tidak valid")

    except KeyboardInterrupt:
        os.system('cls' if os.name == 'nt' else 'clear')
        box("Aplikasi ditutup, semoga sukses 👋👋")
        box("Created By : Thery Vissabil Lillah")