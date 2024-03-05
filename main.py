from web3.middleware import geth_poa_middleware
from client import Client
from constants import MAX_WEI
from data.config import private_key, NITRO_ABI
from models import Polygon
from tasks.nitro import Nitro
from models import TokenAmount
from loguru import logger
import time


def main(private_key: str):
    client = Client(private_key=private_key, network=Polygon)
    client.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    nitro = Nitro(client)

    logger.info('start max USDC.e approve')
    allowance: TokenAmount = nitro.get_allowance()
    if allowance.Wei == MAX_WEI:
        logger.info('already approve max USDC.e')
    else:
        tx = nitro.max_usdce_approve()
        res = client.verif_tx(tx_hash=tx)

        if res:
            logger.info('successful approve max USDC.e')

    usdce_balance = client.balance_of(nitro.usdc_address).Ether
    logger.info(f'USDC.e wallet balance: {usdce_balance}')

    while float(usdce_balance) >= 1.1:
        time.sleep(5)
        quote_swap_data = nitro.quote_swap_data

        tx = nitro.build_tx(quote=quote_swap_data)
        res = nitro.bridge(tx)

        if res:
            usdce_balance = float(usdce_balance) - 1.1
            logger.info(f'USDC.e balance: {usdce_balance}')
        else:
            logger.error('Неполычилось бриджануть, еще раз')

    logger.success('Успешно сбриджил все usdc в blast')


if __name__ == '__main__':
    print('загоняй в роутер по моей рефке https://app.routernitro.com/swap?referal=RT1708192645014')
    main(private_key)
