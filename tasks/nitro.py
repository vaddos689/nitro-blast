import time
import requests
from web3 import Web3
from pyuseragents import random as random_useragent
from client import Client
from data.config import NITRO_ABI
from utils import read_json
from models import TokenAmount
from loguru import logger
from constants import MAX_WEI


class Nitro:
    usdc_address = Web3.to_checksum_address('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174')

    router_abi = read_json(NITRO_ABI)
    router_address = Web3.to_checksum_address('0x8ad970f4e6371cb79140891d45975e8960889f9e')

    def __init__(self, client: Client):
        self.client = client
        self.useragent = random_useragent()
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'access-control-allow-origin': '*',
            'authorization': 'Bearer',
            'content-type': 'application/json',
            'origin': 'https://app.routernitro.com',
            'referer': 'https://app.routernitro.com/',
            'user-agent': self.useragent,
        }
        self.quote_swap_data = self.quote_swap()

    def get_allowance(self):
        res = self.client.get_allowance(Nitro.usdc_address, Nitro.router_address)
        return res

    def quote_swap(self):
        url = 'https://api-beta.pathfinder.routerprotocol.com/api/v2/quote?fromTokenAddress=0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174&toTokenAddress=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&amount=1100000&fromTokenChainId=137&toTokenChainId=81457&partnerId=1&destFuel=0'

        response = requests.get(url, headers=self.headers)

        while True:
            if 'source' in response.json() and response.json()['source']['stableReserveAmount']:
                return response.json()
            elif 'error' in response.json() and response.json()['error'] == 'Insufficient liquidity for the desired asset. Kindly try again later.':
                logger.error('Закончилась ликвидность, повторяю запрос через 10 сек.')
                time.sleep(10)
                return self.quote_swap_data()
            else:
                logger.error('Ошибка при quote_swap request ETH в blast, повторю запрос через 10 сек.')
                time.sleep(10)
                return self.quote_swap_data()

    def build_tx(self, quote: dict):
        url = "https://api-beta.pathfinder.routerprotocol.com/api/v2/transaction"

        quote['senderAddress'] = self.client.address
        quote['receiverAddress'] = self.client.address

        response = requests.post(url=url, headers=self.headers, json=quote)

        if response.json()['txn']['data']:
            return response.json()['txn']

    def max_usdce_approve(self):
        tx = self.client.approve(
                token_address=Nitro.usdc_address,
                spender=Nitro.router_address,
                amount=TokenAmount(amount=MAX_WEI, wei=True)
            )
        return tx

    def bridge(self, txn):
        data = txn['data']
        tx = self.client.send_transaction_nitro(txn=txn, to=Nitro.router_address, data=data)
        res = self.client.verif_tx(tx_hash=tx)
        return res
