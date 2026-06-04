from common.errors import ConfigError


def main():
    print("Hello, World!")

    try:
        raise ConfigError("Test error", details={"key": "value"})
    except ConfigError as e:
        print(e.message)
        print(e.details)

if __name__ == "__main__":
    main()