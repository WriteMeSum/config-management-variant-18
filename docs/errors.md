# Ошибки всех пяти параметров

Воспроизведение: `python3 scripts/demo_errors.py`.
Каждый запуск использует отдельный CSV с одним неверным значением.

```text
package=bad; exit=1
Ошибка: package: нужно groupId:artifactId или A-Z в тестах
repository=ftp://host; exit=1
Ошибка: repository: нужен URL http:// или https://
test_mode=yes; exit=1
Ошибка: test_mode: ожидается true или false
version=[1,2); exit=1
Ошибка: version: нужна фиксированная версия, например 1.0
ascii_tree=1; exit=1
Ошибка: ascii_tree: ожидается true или false
```
