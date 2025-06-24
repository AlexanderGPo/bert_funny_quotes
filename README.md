# Humor Detection: Bert Usage for Detecting Humor in Quotes
## Описание
В этом репозитории представлен продукт, основанный на моделе BERT и позволяющий оценить степень "забавности" цитаты из академической среды.

## Использование
Веса дообученной модели (в качестве основной модели использовался rubert-tiny-2) выложена на Hugging Face Spaces. Использовать модель можно по API:

```python
import requests
url = 'https://kgleba-quotes-inference.hf.space/predict_internal'
data = {
    "text": "текст_цитаты"
}
response = requests.post(url, json=data)

print(response.text) # число в формате float от 0 до 1, где 0 - цитата несмешная, 1 - цитата смешная.
```
## Модель
Архитектура модели, а также словарь и прочие вспомогательные файлы находяться в папке `model`. Скачать веса модели (`model.safetensors`) можно по ссылке. После этого модель может быть развернута локально (`torch.load()`).
## Обучение модели
Процесс обучения BERT-подобной модели представлен в файле `QuotesML_Text_Transofrmation_and_Bert_Training.ipynb`.
## Сайт
В процессе работы над проектом был разработан сайт для автоматической разметки цитат. Его код представлен в папке `quotes-dataset-markup`.
