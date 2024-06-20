#  Pyrofork - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
#
#  This file is part of Pyrofork.
#
#  Pyrofork is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrofork is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrofork.  If not, see <http://www.gnu.org/licenses/>.

import logging

import pyrogram
from pyrogram import raw
from pyrogram import types
from pyrogram.errors import PhoneMigrate, NetworkMigrate
from pyrogram.session import Session, Auth

log = logging.getLogger(__name__)


class SendCode:
    async def send_code(
        self: "pyrogram.Client",
        phone_number: str
    ) -> "types.SentCode":
        """Send the confirmation code to the given phone number.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            phone_number (``str``):
                Phone number in international format (includes the country prefix).

        Returns:
            :obj:`~pyrogram.types.SentCode`: On success, an object containing information on the sent confirmation code
            is returned.

        Raises:
            BadRequest: In case the phone number is invalid.
        """
        phone_number = phone_number.strip(" +")

        while True:
            try:
                r = await self.invoke(
                    raw.functions.auth.SendCode(
                        phone_number=phone_number,
                        api_id=self.api_id,
                        api_hash=self.api_hash,
                        settings=raw.types.CodeSettings()
                    )
                )
            except (PhoneMigrate, NetworkMigrate) as e:
                config = await self.invoke(raw.functions.help.GetConfig())
                for option in config.dc_options:
                    if (option.id == e.value):
                        if option.media_only:
                            if option.ipv6:
                                await self.storage.media_address_v6(option.ip_address)
                            else:
                                await self.storage.media_address(option.ip_address)
                            if option.this_port_only:
                                await self.storage.media_port(option.port)
                        else:
                            if option.ipv6:
                                await self.storage.server_address_v6(option.ip_address)
                            else:
                                await self.storage.server_address(option.ip_address)
                            if option.this_port_only:
                                await self.storage.port(option.port)
                if e not in [2,4] or self.storage.test_mode():
                    await self.storage.media_address(await self.storage.server_address())
                    await self.storage.media_address_v6(await self.storage.server_address_v6())
                    await self.storage.media_port(await self.storage.server_port())
                await self.session.stop()

                await self.storage.dc_id(e.value)
                await self.storage.auth_key(
                    await Auth(
                        self, await self.storage.dc_id(),
                        await self.storage.test_mode(),
                        await self.storage.server_address_v6() if self.ipv6 else await self.storage.server_address(),
                        await self.storage.server_port()
                    ).create()
                )
                self.session = Session(
                    self, await self.storage.dc_id(),
                    await self.storage.auth_key(), await self.storage.test_mode(),
                    await self.storage.server_address_v6() if self.ipv6 else await self.storage.server_address(),
                    await self.storage.server_port()
                )

                await self.session.start()
            else:
                return types.SentCode._parse(r)
