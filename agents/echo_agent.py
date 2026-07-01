"""
echo_agent.py
-------------
Varsayılan (fallback) ajan. Hiçbir uzman ajan mesajı ele alamazsa
bu ajan devreye girer ve genel bir cevap verir.

Neden buna ihtiyaç var?
Router her zaman BİR ajana yönlendirmek zorunda. Eğer hiçbir ajan
mesajı sahiplenmezse bot sessiz kalır ki bu kötü bir kullanıcı deneyimidir.
Bu ajan can_handle içinde her zaman düşük ama sıfırdan büyük bir puan
döndürerek "kimse istemezse ben hallederim" der.

GERÇEK PROJEDE: Burası tam olarak bir LLM'in (OpenAI, Anthropic vb.)
bağlanacağı yerdir. Şu an basit kural tabanlı cevaplar veriyoruz;
handle() metodunu bir API çağrısıyla değiştirmek yeterli olur.
"""

from .base_agent import BaseAgent


class EchoAgent(BaseAgent):
    name = "chat"

    # Basit selamlama sözlüğü (LLM olmadan da bot canlı görünsün diye)
    _GREETINGS = {
        "merhaba": "Merhaba! Sana nasıl yardımcı olabilirim?",
        "selam": "Selam! Bir soru sorabilir veya matematik işlemi yazabilirsin.",
        "hello": "Hello! How can I help you today?",
        "hi": "Hi there! Ask me something or type a math expression.",
    }

    def can_handle(self, message: str) -> float:
        # Fallback ajan: her zaman ele alabilir, ama en düşük öncelikle.
        # Böylece uzman bir ajan varsa o kazanır, yoksa bu devreye girer.
        return 0.1

    def handle(self, message: str) -> str:
        text = message.strip().lower()
        # Bilinen bir selamlama mı?
        for key, reply in self._GREETINGS.items():
            if key in text:
                return reply
        # Değilse genel bir cevap (gerçek projede burada LLM cevabı olur)
        return (
            "Bunu tam anlayamadım ama buradayım. "
            "Matematik işlemi yazabilir (örn: 5 * 8) "
            "veya /help yazarak ne yapabileceğimi görebilirsin."
        )
