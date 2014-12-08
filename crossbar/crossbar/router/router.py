###############################################################################
##
##  Copyright (C) 2014 Tavendo GmbH
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License, version 3,
##  as published by the Free Software Foundation.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##  GNU Affero General Public License for more details.
##
##  You should have received a copy of the GNU Affero General Public License
##  along with this program. If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

from __future__ import absolute_import

from autobahn.wamp import types
from autobahn.wamp import message
from autobahn.wamp.exception import ProtocolError
from autobahn.wamp.interfaces import IRouter, IRouterFactory


class Router:
   """
   Basic WAMP router.

   This class implements :class:`autobahn.wamp.interfaces.IRouter`.
   """

   def __init__(self, factory, realm, options = None):
      """

      :param factory: The router factory this router was created by.
      :type factory: Object that implements :class:`autobahn.wamp.interfaces.IRouterFactory`..
      :param realm: The realm this router is working for.
      :type realm: str
      :param options: Router options.
      :type options: Instance of :class:`autobahn.wamp.types.RouterOptions`.
      """
      self.debug = False
      self.factory = factory
      self.realm = realm
      self._options = options or types.RouterOptions()
      self._broker = self.broker(self, self._options)
      self._dealer = self.dealer(self, self._options)
      self._attached = 0


   def attach(self, session):
      """
      Implements :func:`autobahn.wamp.interfaces.IRouter.attach`
      """
      self._broker.attach(session)
      self._dealer.attach(session)
      self._attached += 1

      return [self._broker._role_features, self._dealer._role_features]


   def detach(self, session):
      """
      Implements :func:`autobahn.wamp.interfaces.IRouter.detach`
      """
      self._broker.detach(session)
      self._dealer.detach(session)
      self._attached -= 1
      if not self._attached:
         self.factory.onLastDetach(self)


   def process(self, session, msg):
      """
      Implements :func:`autobahn.wamp.interfaces.IRouter.process`
      """
      if self.debug:
         print("Router.process: {0}".format(msg))

      ## Broker
      ##
      if isinstance(msg, message.Publish):
         self._broker.processPublish(session, msg)

      elif isinstance(msg, message.Subscribe):
         self._broker.processSubscribe(session, msg)

      elif isinstance(msg, message.Unsubscribe):
         self._broker.processUnsubscribe(session, msg)

      ## Dealer
      ##
      elif isinstance(msg, message.Register):
         self._dealer.processRegister(session, msg)

      elif isinstance(msg, message.Unregister):
         self._dealer.processUnregister(session, msg)

      elif isinstance(msg, message.Call):
         self._dealer.processCall(session, msg)

      elif isinstance(msg, message.Cancel):
         self._dealer.processCancel(session, msg)

      elif isinstance(msg, message.Yield):
         self._dealer.processYield(session, msg)

      elif isinstance(msg, message.Error) and msg.request_type == message.Invocation.MESSAGE_TYPE:
         self._dealer.processInvocationError(session, msg)

      else:
         raise ProtocolError("Unexpected message {0}".format(msg.__class__))


   def authorize(self, session, uri, action):
      """
      Implements :func:`autobahn.wamp.interfaces.IRouter.authorize`
      """
      if self.debug:
         print("Router.authorize: {0} {1} {2}".format(session, uri, action))
      return True


   def validate(self, payload_type, uri, args, kwargs):
      """
      Implements :func:`autobahn.wamp.interfaces.IRouter.validate`
      """
      if self.debug:
         print("Router.validate: {0} {1} {2} {3}".format(payload_type, uri, args, kwargs))



IRouter.register(Router)



class RouterFactory:
   """
   Basic WAMP Router factory.

   This class implements :class:`autobahn.wamp.interfaces.IRouterFactory`.
   """

   router = Router
   """
   The router class this factory will create router instances from.
   """


   def __init__(self, options = None, debug = False):
      """

      :param options: Default router options.
      :type options: Instance of :class:`autobahn.wamp.types.RouterOptions`.      
      """
      self._routers = {}
      self.debug = debug
      self._options = options or types.RouterOptions()


   def get(self, realm):
      """
      Implements :func:`autobahn.wamp.interfaces.IRouterFactory.get`
      """
      if not realm in self._routers:
         self._routers[realm] = self.router(self, realm, self._options)
         if self.debug:
            print("Router created for realm '{0}'".format(realm))
      return self._routers[realm]


   def onLastDetach(self, router):
      assert(router.realm in self._routers)
      del self._routers[router.realm]
      if self.debug:
         print("Router destroyed for realm '{0}'".format(router.realm))



IRouterFactory.register(RouterFactory)