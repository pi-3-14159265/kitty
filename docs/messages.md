## Messages

### kitty.broadcast

Send a message and keep going. Every `@kitty.when_receive` for that message starts, and this script does not wait for them.

**message:** the message name. The sender and the receiver have to use the same text.

```python
kitty.broadcast("go")
```

### kitty.broadcast_and_wait

Send a message and wait until every script that received it has finished. Use this when the next block should happen after the other sprites are done.

**message:** the message name.

```python
kitty.broadcast_and_wait("go")
```
