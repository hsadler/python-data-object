
import time
import sys
sys.path.append('..')

from data_store.cache_driver.redis_driver import RedisDriver
from data_store.cache_config.redis.master_redis_cache import MasterRedisCache
from testie import Testie
from utils.print import ppp


t = Testie()

redis_driver = RedisDriver(cache_config=MasterRedisCache.get_instance())


######## TEST INTERFACE ########


cache_items = {
	'string': 'my_string',
	'escaped_string': 'line1\nline2',
	'raw_string': r'raw/tstring',
	'binary_string': bin(1234),
	'object_string': repr(bytearray()),
	'integer': 1234,
	'negative_float': -1.234,
	# 'complex': 2+3j, # not json serializable
	'boolean': True,
	'list': [1, 'cats', False],
	'dictionary': {'one': 1, 'two': 2},
	# 'empty_object': object(), # not json serializable
	# 'set': set(), # not json serializable
	# 'tuple': tuple() # serializes to list (array)
}
cache_ttl = 1

# test single items
for cache_key, cache_value in cache_items.items():

	# test set
	set_response = redis_driver.set(
		key=cache_key,
		value=cache_value,
		ttl=cache_ttl
	)
	ppp('set_response for {0}:'.format(cache_key), set_response)
	t.should_be_equal(expected=True, actual=set_response)

	# test get before expiration
	get_response = redis_driver.get(key=cache_key)
	ppp('get_response for {0}:'.format(cache_key), get_response)
	t.should_be_equal(expected=cache_value, actual=get_response)

	# test get after expiration
	time.sleep(2)
	get_response = redis_driver.get(key=cache_key)
	ppp('get_response for {0}:'.format(cache_key), get_response)
	t.should_be_equal(expected=None, actual=get_response)

	# test delete
	redis_driver.set(cache_key, cache_value)
	delete_response = redis_driver.delete(cache_key)
	ppp('delete_response for {0}:'.format(cache_key), delete_response)
	t.should_be_equal(expected=1, actual=delete_response)


# test single item failures
fail_key = 'fail'
fail_val = None

# fail set
fail_set_response = redis_driver.set(
	key=fail_key,
	value=fail_val,
	ttl=1
)
ppp('fail_set_response:', fail_set_response)
t.should_be_equal(expected=False, actual=fail_set_response)

# fail get
fail_get_response = redis_driver.get(key=fail_key)
ppp('fail_get_response:', fail_get_response)
t.should_be_equal(expected=None, actual=fail_get_response)

# fail delete
fail_delete_response = redis_driver.delete(key=fail_key)
ppp('fail_delete_response:', fail_delete_response)
t.should_be_equal(expected=0, actual=fail_delete_response)


# test batching
batch_set_response = redis_driver.batch_set(items=cache_items, ttl=cache_ttl)
ppp('batch_set_response:', batch_set_response)
batch_set_expected = { key: True for key, val in cache_items.items() }
t.should_be_equal(expected=batch_set_expected, actual=batch_set_response)

# test get of single after batch set
cache_key = 'string'
cache_value = cache_items[cache_key]
get_response = redis_driver.get(key=cache_key)
ppp('get_response:', get_response)
t.should_be_equal(expected=cache_value, actual=get_response)

cache_key_list = list(cache_items.keys())
batch_get_response = redis_driver.batch_get(keys=cache_key_list)
ppp('batch_get_response:', batch_get_response)
t.should_be_equal(expected=cache_items, actual=batch_get_response)

batch_delete_response = redis_driver.batch_delete(keys=cache_key_list)
ppp('batch_delete_response:', batch_delete_response)
batch_delete_expected = { key: 1 for key, val in cache_items.items() }
t.should_be_equal(expected=batch_delete_expected, actual=batch_delete_response)


# test batch failures
cache_items['fail'] = None
cache_items[None] = 'fail'

# test batch set fail
fail_batch_set_response = redis_driver.batch_set(
	items=cache_items,
	ttl=cache_ttl
)
ppp('fail_batch_set_response:', fail_batch_set_response)
fail_batch_set_expected = {}
for key, val in cache_items.items():
	if key is None or val is None:
		fail_batch_set_expected[key] = False
	else:
		fail_batch_set_expected[key] = True
t.should_be_equal(
	expected=fail_batch_set_expected,
	actual=fail_batch_set_response
)

# test batch get fail
fail_batch_get_response = redis_driver.batch_get(
	keys=[123, 'key does not exist']
)
ppp('fail_batch_get_response:', fail_batch_get_response)
fail_batch_get_expected = {
	123: None,
	'key does not exist': None
}
t.should_be_equal(
	expected=fail_batch_get_expected,
	actual=fail_batch_get_response
)

# test batch delete fail
fail_batch_delete_response = redis_driver.batch_delete(
	keys=['string', None, 'fail', 123, 'key does not exist']
)
ppp('fail_batch_delete_response:', fail_batch_delete_response)
fail_batch_delete_expected = {
	'string': 1,
	None: 0,
	'fail': 0,
	123: 0,
	'key does not exist': 0
}
t.should_be_equal(
	expected=fail_batch_delete_expected,
	actual=fail_batch_delete_response
)


######## TEST SECOND INSTANTIATION OF DRIVER ########


redis_driver2 = RedisDriver(cache_config=MasterRedisCache.get_instance())
ppp('redis driver cache 1:', redis_driver.cache)
ppp('redis driver cache 2:', redis_driver2.cache)
t.should_be_equal(
	expected=True,
	actual=redis_driver.cache == redis_driver2.cache
)
cache_key = 'list'
found_cache_item = redis_driver2.get(key=cache_key)
ppp('found cache item with redis cache 2:', found_cache_item)
t.should_be_equal(
	expected=cache_items[cache_key],
	actual=found_cache_item
)


######## TEST REDIS SPECIFIC METHODS ########


redis_driver.set(
	key='my_key',
	value='my_value',
	ttl=30
)
redis_keys = redis_driver.get_all_keys()
ppp('all currently set Redis keys:', redis_keys)


t.print_report()

