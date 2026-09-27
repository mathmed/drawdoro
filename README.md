# Repository Coverage



| Name                                                                 |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| app/common/logger.py                                                 |       16 |        0 |    100% |           |
| app/common/settings.py                                               |       20 |        0 |    100% |           |
| app/domain/contracts/adr\_repository.py                              |        4 |        0 |    100% |           |
| app/domain/contracts/comment\_repository.py                          |        4 |        0 |    100% |           |
| app/domain/contracts/diagram\_repository.py                          |        4 |        0 |    100% |           |
| app/domain/contracts/documentation\_page\_repository.py              |        4 |        0 |    100% |           |
| app/domain/contracts/folder\_repository.py                           |        4 |        0 |    100% |           |
| app/domain/contracts/project\_repository.py                          |        4 |        0 |    100% |           |
| app/domain/contracts/template\_repository.py                         |        4 |        0 |    100% |           |
| app/domain/contracts/usecase.py                                      |        5 |        0 |    100% |           |
| app/domain/contracts/workspace\_repository.py                        |        4 |        0 |    100% |           |
| app/domain/entities/models/adr.py                                    |       10 |        0 |    100% |           |
| app/domain/entities/models/base\_model.py                            |        3 |        0 |    100% |           |
| app/domain/entities/models/comment.py                                |        8 |        0 |    100% |           |
| app/domain/entities/models/diagram.py                                |       15 |        0 |    100% |           |
| app/domain/entities/models/documentation\_page.py                    |        9 |        0 |    100% |           |
| app/domain/entities/models/folder.py                                 |       10 |        0 |    100% |           |
| app/domain/entities/models/project.py                                |       10 |        0 |    100% |           |
| app/domain/entities/models/template.py                               |       12 |        0 |    100% |           |
| app/domain/entities/models/workspace.py                              |        9 |        0 |    100% |           |
| app/domain/enums/adr\_status.py                                      |        6 |        0 |    100% |           |
| app/domain/errors/domain\_errors.py                                  |        8 |        0 |    100% |           |
| app/domain/usecases/adr/create\_adr.py                               |       13 |        0 |    100% |           |
| app/domain/usecases/adr/delete\_adr.py                               |       13 |        1 |     92% |        19 |
| app/domain/usecases/adr/get\_adr.py                                  |       14 |        0 |    100% |           |
| app/domain/usecases/adr/list\_adrs.py                                |       10 |        1 |     90% |        17 |
| app/domain/usecases/adr/update\_adr.py                               |       20 |        1 |     95% |        26 |
| app/domain/usecases/comment/create\_comment.py                       |       12 |        2 |     83% |     20-26 |
| app/domain/usecases/comment/delete\_comment.py                       |        9 |        1 |     89% |        16 |
| app/domain/usecases/comment/list\_comments.py                        |       10 |        1 |     90% |        17 |
| app/domain/usecases/diagram/create\_diagram.py                       |       16 |        2 |     88% |     23-31 |
| app/domain/usecases/diagram/delete\_diagram.py                       |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/diagram/get\_diagram.py                          |       14 |        0 |    100% |           |
| app/domain/usecases/diagram/list\_diagrams.py                        |       10 |        1 |     90% |        17 |
| app/domain/usecases/diagram/update\_diagram.py                       |       26 |       10 |     62% |     25-34 |
| app/domain/usecases/documentation/get\_documentation\_page.py        |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/documentation/upsert\_documentation\_page.py     |       11 |        2 |     82% |     18-19 |
| app/domain/usecases/folder/create\_folder.py                         |       12 |        2 |     83% |     19-22 |
| app/domain/usecases/folder/delete\_folder.py                         |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/folder/get\_folder.py                            |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/folder/list\_folders.py                          |       10 |        1 |     90% |        17 |
| app/domain/usecases/folder/update\_folder.py                         |       17 |        6 |     65% |     20-25 |
| app/domain/usecases/project/create\_project.py                       |       12 |        2 |     83% |     19-22 |
| app/domain/usecases/project/delete\_project.py                       |       13 |        0 |    100% |           |
| app/domain/usecases/project/get\_project.py                          |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/project/list\_projects.py                        |       10 |        1 |     90% |        17 |
| app/domain/usecases/project/update\_project.py                       |       17 |        6 |     65% |     20-25 |
| app/domain/usecases/template/create\_template.py                     |       15 |        2 |     87% |     21-27 |
| app/domain/usecases/template/delete\_template.py                     |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/template/get\_template.py                        |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/template/list\_templates.py                      |       11 |        1 |     91% |        17 |
| app/domain/usecases/workspace/create\_workspace.py                   |       10 |        0 |    100% |           |
| app/domain/usecases/workspace/delete\_workspace.py                   |       13 |        4 |     69% |     17-20 |
| app/domain/usecases/workspace/get\_workspace.py                      |       14 |        4 |     71% |     18-21 |
| app/domain/usecases/workspace/list\_workspaces.py                    |       10 |        1 |     90% |        15 |
| app/domain/usecases/workspace/update\_workspace.py                   |       16 |        6 |     62% |     20-25 |
| app/infra/database/models/adr.py                                     |       16 |        0 |    100% |           |
| app/infra/database/models/comment.py                                 |       13 |        0 |    100% |           |
| app/infra/database/models/custom\_shape.py                           |       14 |        0 |    100% |           |
| app/infra/database/models/diagram.py                                 |       19 |        0 |    100% |           |
| app/infra/database/models/documentation\_page.py                     |       12 |        0 |    100% |           |
| app/infra/database/models/folder.py                                  |       14 |        0 |    100% |           |
| app/infra/database/models/project.py                                 |       14 |        0 |    100% |           |
| app/infra/database/models/template.py                                |       15 |        0 |    100% |           |
| app/infra/database/models/user.py                                    |       12 |        0 |    100% |           |
| app/infra/database/models/workspace.py                               |       14 |        0 |    100% |           |
| app/infra/database/models/workspace\_member.py                       |       12 |        0 |    100% |           |
| app/infra/database/repositories/adr\_repository.py                   |       41 |       25 |     39% |17-29, 32-34, 37-38, 41-50, 53-56, 60 |
| app/infra/database/repositories/comment\_repository.py               |       25 |       12 |     52% |16-26, 29-32, 35-38, 42 |
| app/infra/database/repositories/diagram\_repository.py               |       45 |       28 |     38% |17-30, 33-40, 43-49, 52-58, 61-76, 79-87, 91 |
| app/infra/database/repositories/documentation\_page\_repository.py   |       25 |       13 |     48% |16-20, 23-38, 42 |
| app/infra/database/repositories/folder\_repository.py                |       38 |       22 |     42% |17-26, 29-36, 39-45, 48-59, 62-70, 74 |
| app/infra/database/repositories/project\_repository.py               |       38 |       22 |     42% |17-26, 29-36, 39-45, 48-59, 62-70, 74 |
| app/infra/database/repositories/template\_repository.py              |       32 |       18 |     44% |16-26, 29-33, 36-40, 43-48, 52 |
| app/infra/database/repositories/workspace\_repository.py             |       38 |       22 |     42% |17-25, 28-35, 38-41, 44-55, 58-66, 70 |
| app/infra/database/session.py                                        |        9 |        2 |     78% |     13-14 |
| app/main/main.py                                                     |        6 |        0 |    100% |           |
| app/presentation/factories/adr\_factories.py                         |       19 |        0 |    100% |           |
| app/presentation/factories/comment\_factories.py                     |       13 |        0 |    100% |           |
| app/presentation/factories/diagram\_factories.py                     |       19 |        0 |    100% |           |
| app/presentation/factories/documentation\_factories.py               |       10 |        0 |    100% |           |
| app/presentation/factories/folder\_factories.py                      |       19 |        0 |    100% |           |
| app/presentation/factories/project\_factories.py                     |       19 |        0 |    100% |           |
| app/presentation/factories/template\_factories.py                    |       16 |        0 |    100% |           |
| app/presentation/factories/workspace\_factories.py                   |       19 |        0 |    100% |           |
| app/presentation/fastapi/configs/configs.py                          |       16 |        0 |    100% |           |
| app/presentation/fastapi/handlers/domain\_error\_handler.py          |       10 |        0 |    100% |           |
| app/presentation/fastapi/middlewares/request\_logging\_middleware.py |       11 |        0 |    100% |           |
| app/presentation/fastapi/routes/adr\_routes.py                       |       29 |        0 |    100% |           |
| app/presentation/fastapi/routes/comment\_routes.py                   |       19 |        0 |    100% |           |
| app/presentation/fastapi/routes/diagram\_routes.py                   |       29 |        0 |    100% |           |
| app/presentation/fastapi/routes/documentation\_routes.py             |       15 |        0 |    100% |           |
| app/presentation/fastapi/routes/folder\_routes.py                    |       29 |        0 |    100% |           |
| app/presentation/fastapi/routes/health\_routes.py                    |        5 |        0 |    100% |           |
| app/presentation/fastapi/routes/project\_routes.py                   |       29 |        0 |    100% |           |
| app/presentation/fastapi/routes/template\_routes.py                  |       24 |        0 |    100% |           |
| app/presentation/fastapi/routes/websocket\_routes.py                 |        7 |        0 |    100% |           |
| app/presentation/fastapi/routes/workspace\_routes.py                 |       29 |        0 |    100% |           |
| app/presentation/fastapi/schemas/adr\_schemas.py                     |        9 |        0 |    100% |           |
| app/presentation/fastapi/schemas/comment\_schemas.py                 |        7 |        0 |    100% |           |
| app/presentation/fastapi/schemas/diagram\_schemas.py                 |       17 |        0 |    100% |           |
| app/presentation/fastapi/schemas/documentation\_schemas.py           |        6 |        0 |    100% |           |
| app/presentation/fastapi/schemas/folder\_schemas.py                  |        9 |        0 |    100% |           |
| app/presentation/fastapi/schemas/project\_schemas.py                 |        9 |        0 |    100% |           |
| app/presentation/fastapi/schemas/template\_schemas.py                |       10 |        0 |    100% |           |
| app/presentation/fastapi/schemas/workspace\_schemas.py               |        7 |        0 |    100% |           |
| **TOTAL**                                                            | **1538** |  **250** | **84%** |           |


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