# Визуализация трех пакетов

Проверено с D2 0.9.0. Приложение формирует исходный текст D2,
вызывает `d2 --layout=dagre INPUT.d2 OUTPUT.svg` и открывает SVG в браузере.
Графы и подписи просмотрены после рендера. Для воспроизведения:

```sh
make demo
# Открытие каждого изображения:
./run.sh examples/junit.csv --output output/junit
./run.sh examples/commons-text.csv --output output/commons-text
./run.sh examples/commons-io.csv --output output/commons-io
```

D2/SVG сохраняются в `output/` и исключены из Git как артефакты запуска.
Ниже приведено содержимое текстовых визуализаций, включая изолированный
узел пакета без зависимостей.

## JUnit 4.13.2

```d2
direction: down
n0: "junit:junit:4.13.2"
n1: "org.hamcrest:hamcrest-core:1.3"
n0.style.fill: "#dbeafe"
n0.style.stroke: "#2563eb"
n0 -> n1
```

```text
junit:junit:4.13.2
`-- org.hamcrest:hamcrest-core:1.3
```

## Commons Text 1.10.0

```d2
direction: down
n0: "org.apache.commons:commons-text:1.10.0"
n1: "org.apache.commons:commons-lang3:3.12.0"
n0.style.fill: "#dbeafe"
n0.style.stroke: "#2563eb"
n0 -> n1
```

```text
org.apache.commons:commons-text:1.10.0
`-- org.apache.commons:commons-lang3:3.12.0
```

## Commons IO 2.11.0

```d2
direction: down
n0: "commons-io:commons-io:2.11.0"
n0.style.fill: "#dbeafe"
n0.style.stroke: "#2563eb"
```

```text
commons-io:commons-io:2.11.0
```

## Сопоставление с штатной визуализацией Maven

Maven Dependency Plugin `dependency:tree -Dscope=runtime` строит текстовое
дерево. Записанный вывод всех трех запусков находится в
[отчете сравнения](comparison.md). После удаления технического корня
эталонного проекта координаты, версии, направление и число ребер совпали
с D2 и ASCII приложения. SVG представляет тот же граф в виде блоков.

Maven показывает тип `jar` и область `compile`; подписи нашего графа
содержат только groupId, artifactId и version. В графах с общей
зависимостью D2 сохраняет обе входящие связи, ASCII помечает повтор
`[shared]`; Maven может сокращать повторные/конфликтующие ветви.
Это различие представления следует отличать от различия зависимостей.

## Тестовые графы

```sh
./run.sh examples/diamond.csv --output output/diamond
./run.sh examples/cycle.csv --output output/cycle
./run.sh examples/self-cycle.csv --output output/self-cycle
```

Для ромба ASCII-дерево:

```text
A
|-- B
|   `-- D
`-- C
    `-- D [shared]
```

Для цикла:

```text
A
`-- B
    `-- C
        `-- A [cycle]
```

В SVG цикл сохраняется как обратная стрелка.
