
import asyncio 

from captcha import get_smartcaptcha_token
import fcm
import youdo_auth

async def main():

    captcha_token = get_smartcaptcha_token()

    fcm_client = await fcm.create_client()
    fcm_token = fcm_client.credentials["fcm"]["registration"]["token"]

    youdo_auth.main(captcha_token=captcha_token, fcm_token=fcm_token)

    await fcm.start_listener(fcm_client)


if __name__ == "__main__":
    asyncio.run(main())
