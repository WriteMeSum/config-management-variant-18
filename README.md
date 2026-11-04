# Визуализатор зависимостей Maven: вариант 18

Практическая работа по конфигурационному управлению. Python 3.9+.
Получение зависимостей реализуется стандартной библиотекой Python.

## Этап 1: конфигурация

```sh
./run.sh examples/junit.csv
make build
make test
```

CSV имеет заголовок `key,value` и пять обязательных строк:

| Ключ | Значение |
| --- | --- |
| package | Координаты `groupId:artifactId`, в тестовом режиме буквы A-Z |
| repository | HTTP(S) URL Maven либо путь к тестовому файлу от CSV |
| test_mode | `true` или `false` |
| version | Фиксированная версия пакета |
| ascii_tree | `true` или `false` |

Выводятся все пять настроек в виде ключ=значение. Ошибки направляются
в stderr, код возврата 1; ошибки аргументов CLI имеют код 2.
Дубликаты, неизвестные ключи, пропуски и пустые значения запрещены.

`load_config` читает CSV; `read_rows` проверяет его структуру;
`boolean` разбирает флаги; `validate_names` проверяет имя и версию;
`validate_repository` проверяет URL/файл. `main` запускает приложение.

## Этап 2: прямые зависимости

```sh
./run.sh examples/junit.csv --stage 2
# org.hamcrest:hamcrest-core:1.3
./run.sh examples/junit.csv --stage 1
```

`Artifact` хранит координаты и формирует путь POM. `MavenRepository.fetch`
получает XML по HTTP(S); `load` разрешает родительские POM и импорты BOM,
кэширует модели и обнаруживает циклы parent/BOM; `dependencies` возвращает
прямые зависимости. Весь сбор данных использует только `urllib` и
`xml.etree.ElementTree`. Maven, pip и сторонние резолверы не вызываются.

`parse_xml` проверяет XML; `text` читает поле; `expand` разрешает `${...}`;
`coordinates` читает координаты; `properties_for` собирает свойства;
`read_managed` обрабатывает управление версиями; `read_dependency` читает
зависимость; `build_pom` объединяет наследование и локальные определения;
`root_artifact` создает координаты корня из настроек.

Анализируется граф compile/runtime. Области test/provided/system исключены.
Сохраняются optional и exclusions. Версии должны быть фиксированными;
диапазоны, динамические версии и timestamped SNAPSHOT не разрешаются.
Активация профилей, relocation и переопределение репозиториев внутри POM
не реализованы. Для сравнения с Maven следует выбирать runtime scope.
