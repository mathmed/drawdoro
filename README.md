# Repository Coverage



| Name                                                                 |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| app/common/logger.py                                                 |       16 |        0 |    100% |           |
| app/common/settings.py                                               |       19 |        0 |    100% |           |
| app/domain/contracts/example\_database\_contract.py                  |        3 |        0 |    100% |           |
| app/domain/contracts/usecase.py                                      |        5 |        0 |    100% |           |
| app/domain/entities/models/base\_model.py                            |        3 |        0 |    100% |           |
| app/domain/entities/models/example\_model.py                         |        2 |        0 |    100% |           |
| app/domain/errors/domain\_errors.py                                  |        8 |        0 |    100% |           |
| app/domain/usecases/example/create\_example\_usecase.py              |       11 |        0 |    100% |           |
| app/infra/database/example\_database.py                              |        8 |        0 |    100% |           |
| app/main/main.py                                                     |        6 |        0 |    100% |           |
| app/presentation/factories/create\_example\_factory.py               |        4 |        0 |    100% |           |
| app/presentation/fastapi/configs/configs.py                          |       16 |        0 |    100% |           |
| app/presentation/fastapi/handlers/domain\_error\_handler.py          |       10 |        0 |    100% |           |
| app/presentation/fastapi/middlewares/request\_logging\_middleware.py |       11 |        0 |    100% |           |
| app/presentation/fastapi/routes/adr\_routes.py                       |       20 |        4 |     80% |18, 23, 28, 33 |
| app/presentation/fastapi/routes/comment\_routes.py                   |       11 |        1 |     91% |        18 |
| app/presentation/fastapi/routes/diagram\_routes.py                   |       20 |        4 |     80% |18, 23, 28, 33 |
| app/presentation/fastapi/routes/documentation\_routes.py             |       11 |        1 |     91% |        18 |
| app/presentation/fastapi/routes/example\_routes.py                   |        7 |        0 |    100% |           |
| app/presentation/fastapi/routes/folder\_routes.py                    |       20 |        4 |     80% |18, 23, 28, 33 |
| app/presentation/fastapi/routes/health\_routes.py                    |        5 |        0 |    100% |           |
| app/presentation/fastapi/routes/project\_routes.py                   |       20 |        4 |     80% |18, 23, 28, 33 |
| app/presentation/fastapi/routes/template\_routes.py                  |       20 |        4 |     80% |18, 23, 28, 33 |
| app/presentation/fastapi/routes/websocket\_routes.py                 |        7 |        3 |     57% |      8-10 |
| app/presentation/fastapi/routes/workspace\_routes.py                 |       20 |        2 |     90% |    28, 33 |
| **TOTAL**                                                            |  **283** |   **27** | **90%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://github.com/mathmed/drawdoro/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/mathmed/drawdoro/tree/python-coverage-comment-action-data)

This is the one to use if your repository is private or if you don't want to customize anything.



## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.