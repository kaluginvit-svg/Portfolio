# GitHub Actions workflows

Workflow-файлы должны лежать **здесь**: `.github/workflows/*.yml`.

Чтобы Actions **использовал** workflow:

1. **Ветка** — файл должен быть в **дефолтной** ветке репозитория (часто `main` или `master`).  
   Settings → General → Default branch.

2. **Имя файла** — только `.yml` или `.yaml`, например `deploy.yml`.

3. **Структура** — первая строка: `name: ...`, далее `on:`, `jobs:`.

4. После пуша в дефолтную ветку обновите вкладку Actions — workflow должен появиться в списке слева.

5. Если workflow не появляется — откройте файл на GitHub (Code → .github/workflows/deploy.yml), проверьте, что нет ошибок (красные подчёркивания). Проверьте кодировку: файл должен быть UTF-8 без BOM.
