from deskpets import main
import traceback

try:
    if __name__ == "__main__":
        main.main()
except Exception as e:
    print(e)
    traceback.print_exc()