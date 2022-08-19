from src.data import make_dataset
from src.models import train, evaluate, predict


def main():
    make_dataset.main()
    train.main()
    evaluate.main()
    predict.main()


if __name__ == '__main__':
    main()
