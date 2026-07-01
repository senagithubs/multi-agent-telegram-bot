"""
base_agent.py
-------------
Bütün ajanların ortak atası. Her ajan bu sınıftan türer.

Neden böyle bir taban sınıf var?
- Her ajanın ortak bir arayüzü (interface) olsun diye.
- Router, bir ajanın ne yaptığını bilmeden "can_handle" ve "handle"
  metotlarını çağırabilsin diye.
Bu, "polymorphism" (çok biçimlilik) denen bir tasarım prensibidir:
Router her ajana aynı şekilde davranır, ajanlar farklı işler yapar.
"""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Soyut (abstract) temel ajan sınıfı.

    ABC = Abstract Base Class. Bu sınıftan doğrudan nesne üretilemez;
    sadece ondan türeyen alt sınıflar (matematik ajanı, çeviri ajanı vs.)
    kullanılır. Bu, "her ajan şu metotları MUTLAKA yazmalı" demenin yoludur.
    """

    #: Ajanın insan-okunur adı (loglarda ve /agents komutunda görünür)
    name: str = "base"

    @abstractmethod
    def can_handle(self, message: str) -> float:
        """Bu ajan verilen mesajı ne kadar iyi ele alabilir?

        Router her ajana bu soruyu sorar ve en yüksek puanı veren
        ajanı seçer.

        Dönüş: 0.0 ile 1.0 arasında bir güven puanı.
            0.0 = bu mesaj bana göre değil
            1.0 = bu mesaj kesinlikle benim uzmanlık alanım
        """
        raise NotImplementedError

    @abstractmethod
    def handle(self, message: str) -> str:
        """Mesajı işle ve kullanıcıya dönecek cevabı üret."""
        raise NotImplementedError
