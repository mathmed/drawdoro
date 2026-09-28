# Repository Coverage



| Name                                                                     |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| app/common/logger.py                                                     |       16 |        0 |    100% |           |
| app/common/settings.py                                                   |       28 |        0 |    100% |           |
| app/domain/contracts/comment\_repository.py                              |        4 |        0 |    100% |           |
| app/domain/contracts/diagram\_repository.py                              |        4 |        0 |    100% |           |
| app/domain/contracts/documentation\_page\_repository.py                  |        4 |        0 |    100% |           |
| app/domain/contracts/folder\_repository.py                               |        4 |        0 |    100% |           |
| app/domain/contracts/project\_repository.py                              |        4 |        0 |    100% |           |
| app/domain/contracts/token\_verifier.py                                  |        3 |        0 |    100% |           |
| app/domain/contracts/usecase.py                                          |        5 |        0 |    100% |           |
| app/domain/contracts/user\_repository.py                                 |        3 |        0 |    100% |           |
| app/domain/contracts/workspace\_member\_repository.py                    |        5 |        0 |    100% |           |
| app/domain/contracts/workspace\_repository.py                            |        4 |        0 |    100% |           |
| app/domain/entities/models/base\_model.py                                |        3 |        0 |    100% |           |
| app/domain/entities/models/comment.py                                    |        9 |        0 |    100% |           |
| app/domain/entities/models/diagram.py                                    |       13 |        0 |    100% |           |
| app/domain/entities/models/documentation\_page.py                        |        9 |        0 |    100% |           |
| app/domain/entities/models/folder.py                                     |       10 |        0 |    100% |           |
| app/domain/entities/models/identity.py                                   |        2 |        0 |    100% |           |
| app/domain/entities/models/project.py                                    |       10 |        0 |    100% |           |
| app/domain/entities/models/user.py                                       |        8 |        0 |    100% |           |
| app/domain/entities/models/workspace.py                                  |        9 |        0 |    100% |           |
| app/domain/entities/models/workspace\_member.py                          |        9 |        0 |    100% |           |
| app/domain/entities/models/workspace\_member\_details.py                 |        4 |        0 |    100% |           |
| app/domain/enums/workspace\_role.py                                      |        8 |        0 |    100% |           |
| app/domain/errors/domain\_errors.py                                      |       12 |        0 |    100% |           |
| app/domain/usecases/auth/authenticate\_user.py                           |       21 |        0 |    100% |           |
| app/domain/usecases/auth/authorize\_workspace\_access.py                 |       51 |        0 |    100% |           |
| app/domain/usecases/comment/create\_comment.py                           |       12 |        2 |     83% |     20-26 |
| app/domain/usecases/comment/delete\_comment.py                           |        9 |        1 |     89% |        16 |
| app/domain/usecases/comment/list\_comments.py                            |       10 |        1 |     90% |        17 |
| app/domain/usecases/diagram/create\_diagram.py                           |       14 |        2 |     86% |     21-27 |
| app/domain/usecases/diagram/delete\_diagram.py                           |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/diagram/get\_diagram.py                              |       14 |        0 |    100% |           |
| app/domain/usecases/diagram/list\_diagrams.py                            |       10 |        1 |     90% |        17 |
| app/domain/usecases/diagram/update\_diagram.py                           |       22 |        8 |     64% |     23-30 |
| app/domain/usecases/documentation/get\_documentation\_page.py            |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/documentation/upsert\_documentation\_page.py         |       11 |        2 |     82% |     18-19 |
| app/domain/usecases/folder/create\_folder.py                             |       12 |        2 |     83% |     19-22 |
| app/domain/usecases/folder/delete\_folder.py                             |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/folder/get\_folder.py                                |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/folder/list\_folders.py                              |       10 |        1 |     90% |        17 |
| app/domain/usecases/folder/update\_folder.py                             |       17 |        6 |     65% |     20-25 |
| app/domain/usecases/project/create\_project.py                           |       12 |        0 |    100% |           |
| app/domain/usecases/project/delete\_project.py                           |       13 |        0 |    100% |           |
| app/domain/usecases/project/get\_project.py                              |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/project/list\_projects.py                            |       10 |        1 |     90% |        17 |
| app/domain/usecases/project/update\_project.py                           |       17 |        6 |     65% |     20-25 |
| app/domain/usecases/workspace/create\_workspace.py                       |       18 |        0 |    100% |           |
| app/domain/usecases/workspace/delete\_workspace.py                       |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/workspace/get\_workspace.py                          |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/workspace/list\_workspaces.py                        |       21 |        0 |    100% |           |
| app/domain/usecases/workspace/update\_workspace.py                       |       16 |        6 |     62% |     20-25 |
| app/domain/usecases/workspace\_member/add\_workspace\_member.py          |       21 |        0 |    100% |           |
| app/domain/usecases/workspace\_member/list\_workspace\_members.py        |       10 |        0 |    100% |           |
| app/domain/usecases/workspace\_member/remove\_workspace\_member.py       |       24 |        0 |    100% |           |
| app/domain/usecases/workspace\_member/update\_workspace\_member\_role.py |       19 |        0 |    100% |           |
| app/infra/auth/cognito\_token\_verifier.py                               |       31 |        0 |    100% |           |
| app/infra/database/models/comment.py                                     |       13 |        0 |    100% |           |
| app/infra/database/models/custom\_shape.py                               |       14 |        0 |    100% |           |
| app/infra/database/models/diagram.py                                     |       17 |        0 |    100% |           |
| app/infra/database/models/documentation\_page.py                         |       12 |        0 |    100% |           |
| app/infra/database/models/folder.py                                      |       14 |        0 |    100% |           |
| app/infra/database/models/project.py                                     |       14 |        0 |    100% |           |
| app/infra/database/models/user.py                                        |       12 |        0 |    100% |           |
| app/infra/database/models/workspace.py                                   |       14 |        0 |    100% |           |
| app/infra/database/models/workspace\_member.py                           |       12 |        0 |    100% |           |
| app/infra/database/repositories/comment\_repository.py                   |       31 |       16 |     48% |17-27, 30-33, 36-42, 45-48, 52 |
| app/infra/database/repositories/diagram\_repository.py                   |       43 |       26 |     40% |17-28, 31-38, 41-47, 50-56, 59-72, 75-83, 87 |
| app/infra/database/repositories/documentation\_page\_repository.py       |       25 |       13 |     48% |16-20, 23-38, 42 |
| app/infra/database/repositories/folder\_repository.py                    |       38 |       22 |     42% |17-26, 29-36, 39-45, 48-59, 62-70, 74 |
| app/infra/database/repositories/project\_repository.py                   |       38 |       19 |     50% |25-26, 29-36, 39-45, 48-59, 62-70, 74 |
| app/infra/database/repositories/user\_repository.py                      |       27 |       15 |     44% |14-16, 19-23, 26-31, 35 |
| app/infra/database/repositories/workspace\_member\_repository.py         |       40 |       21 |     48% |19-26, 29-35, 43-52, 55-62, 65-68, 71-77, 81 |
| app/infra/database/repositories/workspace\_repository.py                 |       46 |       27 |     41% |18-26, 29-36, 39-42, 45-50, 53-59, 62-73, 76-84, 88 |
| app/infra/database/session.py                                            |        9 |        0 |    100% |           |
| app/infra/realtime/connection\_manager.py                                |       49 |        0 |    100% |           |
| app/main/main.py                                                         |        6 |        0 |    100% |           |
| app/presentation/factories/auth\_factories.py                            |       23 |        0 |    100% |           |
| app/presentation/factories/comment\_factories.py                         |       13 |        0 |    100% |           |
| app/presentation/factories/diagram\_factories.py                         |       19 |        0 |    100% |           |
| app/presentation/factories/documentation\_factories.py                   |       10 |        0 |    100% |           |
| app/presentation/factories/folder\_factories.py                          |       19 |        0 |    100% |           |
| app/presentation/factories/project\_factories.py                         |       19 |        0 |    100% |           |
| app/presentation/factories/workspace\_factories.py                       |       20 |        0 |    100% |           |
| app/presentation/factories/workspace\_member\_factories.py               |       17 |        4 |     76% |20, 26, 32, 38 |
| app/presentation/fastapi/configs/configs.py                              |       21 |        0 |    100% |           |
| app/presentation/fastapi/dependencies/current\_user.py                   |       15 |        0 |    100% |           |
| app/presentation/fastapi/dependencies/workspace\_access.py               |       31 |        2 |     94% |     26-28 |
| app/presentation/fastapi/handlers/domain\_error\_handler.py              |       10 |        0 |    100% |           |
| app/presentation/fastapi/middlewares/request\_logging\_middleware.py     |       11 |        0 |    100% |           |
| app/presentation/fastapi/routes/auth\_routes.py                          |       11 |        0 |    100% |           |
| app/presentation/fastapi/routes/comment\_routes.py                       |       22 |        0 |    100% |           |
| app/presentation/fastapi/routes/diagram\_routes.py                       |       30 |        0 |    100% |           |
| app/presentation/fastapi/routes/documentation\_routes.py                 |       16 |        0 |    100% |           |
| app/presentation/fastapi/routes/folder\_routes.py                        |       30 |        0 |    100% |           |
| app/presentation/fastapi/routes/health\_routes.py                        |        5 |        0 |    100% |           |
| app/presentation/fastapi/routes/project\_routes.py                       |       30 |        0 |    100% |           |
| app/presentation/fastapi/routes/websocket\_routes.py                     |       47 |        2 |     96% |    37, 46 |
| app/presentation/fastapi/routes/workspace\_member\_routes.py             |       26 |        0 |    100% |           |
| app/presentation/fastapi/routes/workspace\_routes.py                     |       32 |        0 |    100% |           |
| app/presentation/fastapi/schemas/comment\_schemas.py                     |        7 |        0 |    100% |           |
| app/presentation/fastapi/schemas/diagram\_schemas.py                     |       13 |        0 |    100% |           |
| app/presentation/fastapi/schemas/documentation\_schemas.py               |        6 |        0 |    100% |           |
| app/presentation/fastapi/schemas/folder\_schemas.py                      |        9 |        0 |    100% |           |
| app/presentation/fastapi/schemas/project\_schemas.py                     |        9 |        0 |    100% |           |
| app/presentation/fastapi/schemas/user\_schemas.py                        |        4 |        0 |    100% |           |
| app/presentation/fastapi/schemas/workspace\_member\_schemas.py           |        8 |        0 |    100% |           |
| app/presentation/fastapi/schemas/workspace\_schemas.py                   |        7 |        0 |    100% |           |
| **TOTAL**                                                                | **1724** |  **234** | **86%** |           |


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