# The MIT License (MIT)
#
# Copyright (c) 2015 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Erik Hvatum <ice.rikh@gmail.com>

import numpy
from PyQt5 import Qt

class Property(property):
    """A convenience class for making properties that have a default value and a change Qt-signal.  An
    example of a class with two Property attributes, with the default value of the "bar" Property
    depending on the value of "foo" (if .foo is None, .bar defaults to 42):

    class C(Qt.QObject):
        changed = Qt.pyqtSignal(object)

        def __init__(self, parent=None):
            super().__init__(parent)
            for property in self.properties:
                property.instantiate(self)

        properties = []

        foo = Property(
            properties,
            "foo",
            default_value_callback=lambda c_instance: None,
            take_arg_callback=lambda c_instance, in_: None if (in_ is None or in_ == '') else str(in_),
            post_set_callback=lambda c_instance, in_: c_instance.__class__.bar.update_default(c_instance),
            doc="From wiktionary: \"[foo is a] metasyntactic variable used to represent an unspecified entity. "
                "If part of a series of such entities, it is often the first in the series, and followed immediately by bar.\"")

        bar = Property(
            properties,
            "bar",
            default_value_callback=lambda c_instance: None if c_instance.foo is None else 42)

        for property in properties:
            exec(property.changed_signal_name + ' = Qt.pyqtSignal(object)')
        del property

    c = C()
    c.bar_changed.connect(lambda: print("bar's apparent value changed to:", c.bar))
    print(c.foo, c.bar)  # -> None None
    c.foo='baz'  # -> bar's apparent value changed to: 42
    print(c.foo, c.bar)  # -> baz 42
    c.bar=55     # -> bar's apparent value changed to: 55
    print(c.foo, c.bar)  # -> baz 55
    del c.foo
    print(c.foo, c.bar)  # -> None 55
    del c.bar
    bar's apparent value changed to: None
    print(c.foo, c.bar)  # -> None None

    Additionally, if the class bearing a Property has a .changed attribute and that .changed attribute is a Qt
    signal, a_property.instantiate(bearer) connects the a_changed signal created for that property with the .changed signal.

    NB: Property is derived from "property" for the sole reason that IPython's question-mark magic is special-cased for
    properties.  Deriving from property causes Property to receive the same treatment, providing useful output for
    something.prop? in IPython (where prop is a Property instance)."""
    def __init__(self, properties, name, default_value_callback, take_arg_callback=None, pre_set_callback=None, post_set_callback=None, doc=None):
        self.name = name
        self.var_name = '_' + name
        self.default_val_var_name = '_default_' + name
        self.changed_signal_name = name + '_changed'
        self.default_value_callback = default_value_callback
        self.take_arg_callback = take_arg_callback
        self.pre_set_callback = pre_set_callback
        self.post_set_callback = post_set_callback
        if doc is not None:
            self.__doc__ = doc
        properties.append(self)

    @staticmethod
    def eq(a, b):
        r = a == b
        if isinstance(r, bool):
            return r
        if isinstance(r, numpy.bool_):
            return bool(r)
        return all(r)

    def instantiate(self, obj):
        setattr(obj, self.default_val_var_name, self.default_value_callback(obj))
        if hasattr(obj, 'changed') and isinstance(obj.changed, Qt.pyqtBoundSignal):
            getattr(obj, self.changed_signal_name).connect(obj.changed)

    def update_default(self, obj):
        if hasattr(obj, self.var_name):
            # An explicitly set value is overriding the default, so even if the default has changed, the apparent value of the property has not
            setattr(obj, self.default_val_var_name, self.default_value_callback(obj))
        else:
            # The default value is the apparent value, meaning that we must check if the default has changed and signal an apparent value change
            # if it has
            old_default = getattr(obj, self.default_val_var_name)
            new_default = self.default_value_callback(obj)
            if not self.eq(new_default, old_default):
                setattr(obj, self.default_val_var_name, new_default)
                getattr(obj, self.changed_signal_name).emit(obj)

    def copy_instance_value(self, src_obj, dst_obj):
        """Replace value for this property in dst_obj if src_obj has a non-default value
        for this property."""
        try:
            v = getattr(src_obj, self.var_name)
        except AttributeError:
            return
        setattr(dst_obj, self.var_name, v)

    def __get__(self, obj, _=None):
        if obj is None:
            return self
        try:
            return getattr(obj, self.var_name)
        except AttributeError:
            return getattr(obj, self.default_val_var_name)

    def __set__(self, obj, v):
        if self.take_arg_callback is not None:
            v = self.take_arg_callback(obj, v)
        if not hasattr(obj, self.var_name) or not self.eq(v, getattr(obj, self.var_name)):
            if self.pre_set_callback is not None:
                if self.pre_set_callback(obj, v) == False:
                    return
            setattr(obj, self.var_name, v)
            if self.post_set_callback is not None:
                self.post_set_callback(obj, v)
            getattr(obj, self.changed_signal_name).emit(obj)

    def __delete__(self, obj):
        """Reset to default value by way of removing the explicitly set override, causing the apparent value to be default."""
        try:
            old_value = getattr(obj, self.var_name)
            delattr(obj, self.var_name)
            new_value = getattr(obj, self.default_val_var_name)
            if not self.eq(old_value, new_value):
                if self.post_set_callback is not None:
                    self.post_set_callback(obj, new_value)
                getattr(obj, self.changed_signal_name).emit(obj)
        except AttributeError:
            # Property was already using default value
            pass

    def is_default(self, obj):
        if not hasattr(obj, self.var_name):
            return True
        val = getattr(obj, self.var_name)
        def_val = getattr(obj, self.default_val_var_name)
        eq = self.eq(val, def_val)
        return eq