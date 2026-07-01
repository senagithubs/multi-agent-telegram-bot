"""
core/web.py
-----------
Flask tabanlı webhook sunucusu.

İki çalışma modu vardır:
- POLLING: bot Telegram'a sürekli "yeni mesaj var mı?" diye sorar.
  Geliştirmede kolaydır.
- WEBHOOK: Telegram, yeni mesaj geldiğinde bizim sunucumuza HTTP POST
  atar. Üretimde (production) tercih edilir çünkü daha ölçeklenebilir
  ve gerçek zamanlıdır.

Bu modül webhook modunu ve ayrıca bir /health endpoint'i sağlar
(deploy ortamlarında botun ayakta olup olmadığını kontrol için).
"""

import logging

from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)


def create_flask_app(update_processor) -> Flask:
    """Webhook isteklerini işleyen Flask uygulamasını oluşturur.

    update_processor: gelen Telegram update sözlüğünü işleyecek fonksiyon.
    """
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        # Deploy platformlarının (Railway, Render, vb.) sağlık kontrolü
        return jsonify({"status": "ok"}), 200

    @app.route("/webhook", methods=["POST"])
    def webhook():
        # Telegram'dan gelen JSON güncellemesini al ve işle
        update_data = request.get_json(force=True, silent=True)
        if update_data is None:
            return jsonify({"error": "invalid payload"}), 400
        try:
            update_processor(update_data)
        except Exception as exc:
            logger.exception("Webhook işlenirken hata: %s", exc)
            # Telegram'a 200 dön ki mesajı tekrar tekrar göndermesin;
            # hatayı biz loglayıp içeride hallederiz.
            return jsonify({"status": "error_logged"}), 200
        return jsonify({"status": "ok"}), 200

    return app
