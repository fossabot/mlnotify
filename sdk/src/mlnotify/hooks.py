from functools import partial, partialmethod
import inspect
from typing import Any, Callable, Type, Union

import gorilla

from mlnotify.logger import logger

HookFunction = Callable

GORILLA_SETTINGS = gorilla.Settings(allow_hit=True, store_hit=True)


def base_patch_func(*args, __original_func: Callable, __before: HookFunction, __after: HookFunction, **kwargs) -> Any:
    """When patching a method, this function will run instead.

    Args:
        __original_func (Callable): The original function before the patch
        __before (HookFunction): The function to run before the original function
        __after (HookFunction): The function to run after the original function
        *args: positional args passed for the original function
        **kwargs: keyword args passed for the original function

    Returns:
        result (Any): The original function's result
    """
    logger.debug("Running patched func", args, kwargs)

    try:
        __before()
    except Exception as e:
        logger.debug("Failed to run hook function (before)", e)

    res = __original_func(*args, **kwargs)

    try:
        __after()
    except Exception as e:
        logger.debug("Failed to run hook function (after)", e)

    return res


def patch(destination: Any, name: str, before: HookFunction, after: HookFunction) -> None:
    """This function patches the destination.name function and replaces it with the base_patch_func.

    Args:
        destination (Any): The class/dict to patch
        name (str): The function name to be replaced
        before (HookFunction): The function to run before the original function
        after (HookFunction): The function to run after the original function
    """
    original_func: Callable = gorilla.get_attribute(destination, name)

    partial_type: Union[Type[partial], Type[partialmethod]] = partialmethod if inspect.isclass(destination) else partial

    patch_func = partial_type(base_patch_func, __original_func=original_func, __before=before, __after=after)
    patch = gorilla.Patch(destination, name, patch_func, settings=GORILLA_SETTINGS)
    gorilla.apply(patch)


def apply_hooks(before: HookFunction, after: HookFunction):
    """Applys hooks.

    This function applies all hooks - imports the relevant packages and patches
    the specified functions. Since usually not all packages exist, it runs on
    a best-effort assumption.

    Args:
        before (HookFunction): The function to run before the original function
        after (HookFunction): The function to run after the original function
    """
    logger.debug("Applying hooks")

    try:
        import lightgbm

        patch(lightgbm, "train", before=before, after=after)
        patch(lightgbm.sklearn, "train", before=before, after=after)
    except Exception as e:
        logger.debug("Could not import and patch lightgbm", e)
    try:
        import xgboost

        patch(xgboost, "train", before=before, after=after)
        patch(xgboost.sklearn, "train", before=before, after=after)
    except Exception as e:
        logger.debug("Could not import and patch xgboost", e)
    try:
        import tensorflow

        patch(tensorflow.keras.Model, "fit", before=before, after=after)
        patch(tensorflow.keras.Model, "train_on_batch", before=before, after=after)
    except Exception as e:
        logger.debug("Could not import and patch tensorflow.keras", e)
        # If tensorflow.keras patching doesn't work, we can try
        # patching keras as a standalone
        try:
            import keras

            patch(keras.Model, "fit", before=before, after=after)
            patch(keras.Model, "train_on_batch", before=before, after=after)
        except Exception as e:
            logger.debug("Could not import and patch keras", e)
    try:
        import sklearn.svm
        import sklearn.tree

        patch(sklearn.svm.SVC, "fit", before=before, after=after)
        patch(sklearn.svm.SVR, "fit", before=before, after=after)
        patch(sklearn.svm.OneClassSVM, "fit", before=before, after=after)
        patch(sklearn.svm.NuSVC, "fit", before=before, after=after)
        patch(sklearn.svm.NuSVR, "fit", before=before, after=after)
        patch(sklearn.svm.LinearSVR, "fit", before=before, after=after)
        patch(sklearn.svm.LinearSVC, "fit", before=before, after=after)
        patch(sklearn.tree.DecisionTreeClassifier, "fit", before=before, after=after)
        patch(sklearn.tree.DecisionTreeRegressor, "fit", before=before, after=after)
    except ImportError as e:
        logger.debug("Could not import and patch sklearn", e)
