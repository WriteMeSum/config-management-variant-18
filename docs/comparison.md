# Сравнение с Maven

Проверка выполнена 5 ноября 2026 года на Maven 3.10.0,
Maven Dependency Plugin 3.8.1, репозиторий Maven Central.

## Воспроизведение

```sh
mvn --version
python3 scripts/compare_maven.py
./run.sh examples/junit.csv --stage 4
./run.sh examples/commons-text.csv --stage 4
./run.sh examples/commons-io.csv --stage 4
```

Скрипт создает временный POM с одной исследуемой зависимостью и вызывает:

```sh
mvn -B -q -f /path/to/pom.xml \
  org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree \
  -Dscope=runtime -DoutputType=text -DoutputFile=/path/to/reference.txt
```

Maven используется исключительно как независимый эталон. Приложение
получает POM непосредственно по HTTP и не читает результаты Maven.

## Полученные результаты

| Пакет | Транзитивные зависимости приложения и Maven | Порядок приложения |
| --- | --- | --- |
| junit:junit:4.13.2 | org.hamcrest:hamcrest-core:1.3 | hamcrest-core, junit |
| commons-text:1.10.0 | commons-lang3:3.12.0 | commons-lang3, commons-text |
| commons-io:commons-io:2.11.0 | Нет runtime-зависимостей | commons-io |

Полные координаты и области видимости приведены в исходном выводе:

- [JUnit](comparison/junit-maven.txt).
- [Commons Text](comparison/commons-text-maven.txt).
- [Commons IO](comparison/commons-io-maven.txt).

Во всех трех случаях множества узлов и ребер совпадают после удаления
технического корня `example:comparison:1.0`, введенного эталонным скриптом.
Maven рисует зависимый пакет перед его зависимостями. Порядок этапа 4
обратный по смыслу: сначала зависимости, затем сам пакет. Расхождение
последовательностей связано с назначением вывода, а не с различием графов.
Maven `dependency:tree` описывает дерево, а не хронологию скачивания;
на сетевую последовательность влияют кэш и внутренняя работа Maven.

## Ограничения сравнения

Анализируется compile/runtime граф фиксированных версий. Maven может
выбирать ближайшую версию при конфликте, учитывать активные профили,
relocation, тип/классификатор артефакта, настройки и дополнительные
репозитории. Наш инструмент показывает граф объявленных зависимостей
с отдельными узлами для разных версий и не воспроизводит все эти механизмы.
На выбранных примерах конфликтов версий нет.

Не поддерживаются диапазоны и динамические версии, разрешение SNAPSHOT
через maven-metadata.xml, активация профилей и relocation. При неизвестной
версии/свойстве приложение возвращает ошибку, а не подставляет значение.
Свойства parent вычисляются в контексте parent: сложное переопределение
свойств унаследованных зависимостей в child не моделируется полностью.

Семантика Maven:
[Dependency mechanism](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html),
[POM Reference](https://maven.apache.org/pom.html).
