__HOOK_REGISTRY = {}
__PRE_HOOK_REGISTRY = {}
__POST_HOOK_REGISTRY = {}

def add_to_registry(func, category):
    global __HOOK_REGISTRY

    if not category in __HOOK_REGISTRY:
        __HOOK_REGISTRY[category] = [func]
    else:
        __HOOK_REGISTRY[category].append(func)

def add_to_pre_registry(func, cmd_name):
    global __PRE_HOOK_REGISTRY

    if not cmd_name in __PRE_HOOK_REGISTRY:
        __PRE_HOOK_REGISTRY[cmd_name] = [func]
    else:
        __PRE_HOOK_REGISTRY[cmd_name].append(func)

def add_to_post_registry(func, cmd_name):
    global __POST_HOOK_REGISTRY

    if not cmd_name in __POST_HOOK_REGISTRY:
        __POST_HOOK_REGISTRY[cmd_name] = [func]
    else:
        __POST_HOOK_REGISTRY[cmd_name].append(func)

def get_registry_categories():
    global __HOOK_REGISTRY

    return __HOOK_REGISTRY.keys()

def get_registry_category(categorie):
    global __HOOK_REGISTRY

    return __HOOK_REGISTRY[categorie]

def get_pre_hooks(cmd_name):
    global __PRE_HOOK_REGISTRY
    return __PRE_HOOK_REGISTRY.get(cmd_name, None)

def get_post_hooks(cmd_name):
    global __POST_HOOK_REGISTRY
    return __POST_HOOK_REGISTRY.get(cmd_name, None)

def post_configure(f, *a, **kw):
    add_to_registry((f, a, kw), "post_configure")
    add_to_post_registry((f, a, kw), "configure")

def pre_configure(f, *a, **kw):
    add_to_registry((f, a, kw), "pre_configure")
    add_to_pre_registry((f, a, kw), "configure")
