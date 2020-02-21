# Message Staging Service

```text
                     validate message
                             v
(plugin) -> [|||] -> (message staging service) -> [|||] -> (shovel) -> beehive
              ^                                     ^
           messages                             to-beehive
```

This service is responsible for validating the node ID and sub ID in messages published by plugins, before they are shoveled to beehive.
