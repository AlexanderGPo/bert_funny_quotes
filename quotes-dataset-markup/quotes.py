import os
import re

__all__ = ['GenericQuote', 'LetovoQuote', 'MyxaQuote', 'HSEQuote', 'FEFUQuote', 'KSUQuote', 'ISUQuote', 'MGTUQuote', 'MIPTQuote',
           'SGUQuote', 'VKLetovoQuote', 'NSTUQuote', 'SFEDUQuote', 'URFUQuote', 'MSUQuote', 'search_profanity']

if os.getenv('PRODUCTION') is None:
    from check_swear import SwearingCheck

    profanity_checker = SwearingCheck()


class GenericQuote:
    channel_link: str = ''
    channel_name: str = ''
    MAX_QUOTE_LEN: int = 100_000

    def __init__(self, text: str):
        self.text = text.strip()
        assert self.text, 'Text is empty!'
        assert '#' in self.text, 'Text is most likely not a quote (does not contain hashtag)!'

        self.tags = ''

        self.refactor()

    # Refactor approaches
    def _unify_dashes(self):
        self.text = re.sub(r'^ *[-–—−‒⁃]+ *', r'— ', self.text, flags=re.MULTILINE)

    def _remove_dangling_dash(self):
        if self.text.count('—') == 1:
            self.text = re.sub(r'^— ', r'', self.text, flags=re.MULTILINE)

    def _separate_tags(self):
        while '#' in self.text:
            start = self.text.find('#') + 1
            stop_symbols = (' ', '\n', '\t', '#')
            next_stop = [self.text.find(symbol, start) % self.MAX_QUOTE_LEN for symbol in stop_symbols]
            end = min(next_stop)

            author = self.text[start:end].capitalize().replace('ё', 'е')

            self.tags += f'#{author} '
            self.text = self.text[:start - 1].strip() + self.text[end:].strip()

    def _prohibit_links(self):
        # Implementation borrowed from the `validators` library
        assert not re.search(
            # First character of the domain
            rf"(?:[a-z0-9]"
            # Sub-domain
            + rf"(?:[a-z0-9-]{{0,61}}"
            # Hostname
            + rf"[a-z0-9])?\.)"
            # First 61 characters of the gTLD
            + r"+[a-z0-9][a-z0-9-_]{0,61}"
            # Last character of the gTLD
            + rf"[a-z]",
            self.text,
            re.IGNORECASE
        ), 'Link found!'

    def _remove_quotation_marks(self):
        self.text = re.sub(r'^"([^"]+)"$', r'\1', self.text)
        self.text = re.sub(r"^'([^'])+'$", r'\1', self.text)

    def refactor(self):
        pass

    def __str__(self) -> str:
        return self.text


class LetovoQuote(GenericQuote):
    channel_link: str = 'https://t.me/letovo_quotes'
    channel_name: str = 'Забавные цитаты Летово'

    def _remove_junk_tags(self):
        junk_tags = ['встречакоманд', 'я', '"]', '\'"]}', 'aa', 'fuckers', 'heheheha', 'meow', 'rus_8_26', 'studentseng_8_ph4point1',
                     'test', 'aboba', 'artificial_intelligence', 'bro', 'lasttest', 'meow', 'new', 'sorry', 'test', 'testmeow',
                     'английский', 'аноним', 'анонимно', 'богдан', 'бординг', 'боря_бука_а_мисюрий_отклоняет_цитаты', 'ведущий',
                     'выездколоменское', 'выпускник', 'дебаты', 'девятиклассник', 'знаменитый_учитель_по_информатике', 'какойточел',
                     'летовожабы', 'майскийкросс', 'мисюрий_бука_и_отклоняет_цитаты', 'мнепожалуйста', 'мостюф', 'мюзикл',
                     'наш_лучший_учитель', 'неизвестныйгений', 'ну_а_че_глебу_можно_а_мне_нельзя', 'одобряю', 'поднятиефлага', 'почему?',
                     'прекратитьпроизволадминов', 'простите',
                     'степанов\n\n\nадмины простите думаю нужны пояснения. это он говорит про осадок, который обозначается стрелкой вниз',
                     'ура_обнова', 'ученики', 'учитель', 'фотосессич', 'хаусмастер', 'хаусмастер_6', 'хватит', 'цитатник', 'широкийкость',
                     'ярмаркасообществ', 'авторнеизвестен', 'аноним', 'бот', 'бот говно', 'вопрос', 'восьмойкласс', 'вселидома?',
                     'деньвыездов', 'жестокаяправда', 'задержкавразвитии', 'кашинкалязин', 'кринж', 'кто-то с летовской среды', 'кчау',
                     'лютыйбот', 'не', 'некринж', 'остановкавразвитии', 'отклонениеотнормы', 'отклониевпользунормы', 'пожалуйста',
                     'простите', 'профматы', 'рабочие', 'тест', 'тест предложки', 'тяжело', 'ужас', 'ученики8базыхимии', 'хехе', 'хештег',
                     'хуй', 'цитата (сейчас отклоню)', 'я', 'калимуллина-нечаева']

        assert not any(f'#{tag}' in self.text.lower() for tag in junk_tags), 'Found junk tags!'

    def refactor(self):
        self._remove_junk_tags()
        self._unify_dashes()
        self._remove_dangling_dash()
        self._separate_tags()


class MyxaQuote(GenericQuote):
    channel_link: str = 'https://vk.com/citatnik_myxa'
    channel_name: str = 'Цитаты преподавателей Штиглица (Мухи)'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class HSEQuote(GenericQuote):
    channel_link: str = 'https://vk.com/hseteachers'
    channel_name: str = 'Цитатник ВШЭ'

    def _remove_brace_tag(self):
        self.text = re.sub(r'\([^)]+\)$', r'', self.text)
        self.text = self.text.strip()

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_brace_tag()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class FEFUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/fefu_quotes'
    channel_name: str = 'Цитаты преподавателей ДВФУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class KSUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/glagolit_ksu'
    channel_name: str = 'Цитаты преподавателей КФУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class ISUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/isu_quotes'
    channel_name: str = 'Цитаты преподавателей ИГУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class MGTUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/mgtupage'
    channel_name: str = 'Цитаты преподавателей МГТУ им. Н.Э. Баумана'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class MIPTQuote(GenericQuote):
    channel_link: str = 'https://vk.com/prepod_mipt'
    channel_name: str = 'Цитаты преподавателей МФТИ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class SGUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/public80867350'
    channel_name: str = 'Цитаты великих преподавателей СГУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class VKLetovoQuote(GenericQuote):
    channel_link: str = 'https://vk.com/public170539958'
    channel_name: str = 'Цитаты преподавателей Летово'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class NSTUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/quotes_nstu'
    channel_name: str = 'Цитаты преподавателей НГТУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class SFEDUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/sfeduquotes'
    channel_name: str = 'Цитаты преподавателей ЮФУ (SFEDU)'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class URFUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/urfusay'
    channel_name: str = 'Цитаты преподавателей УрФУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


class MSUQuote(GenericQuote):
    channel_link: str = 'https://vk.com/ustami_msu'
    channel_name: str = 'Цитаты преподавателей МГУ'

    def refactor(self):
        self._prohibit_links()
        self._separate_tags()
        self._remove_quotation_marks()
        self._unify_dashes()
        self._remove_dangling_dash()


def search_profanity(dataset: list[GenericQuote], exclude: bool = True) -> list[GenericQuote]:
    dataset_prediction = profanity_checker.predict(list(map(lambda quote: quote.text, dataset)))
    return [dataset[index] for index, verdict in enumerate(dataset_prediction) if verdict ^ exclude]
