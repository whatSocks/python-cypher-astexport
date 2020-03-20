import ast
import json


def export_json(tree, pretty_print=False):
    if not isinstance(tree, ast.AST):
        raise ValueError(
            "The argument of export_json(..) must be of type AST, not '{}'".format(
                type(tree)
            )
        )
    return json.dumps(
        export_dict(tree),
        indent=4 if pretty_print else None,
        sort_keys=True,
        separators=(",", ": ") if pretty_print else (",", ":")
    )


def export_dict(tree):
    if not isinstance(tree, ast.AST):
        raise ValueError(
            "The argument of export_dict(..) must be of type AST, not '{}'".format(
                type(tree)
            )
        )
    return DictExportVisitor().visit(tree)


class DictExportVisitor:
    ast_type_field = "ast_type"

    def visit(self, node):
        node_type = node.__class__.__name__
        meth = getattr(self, "visit_" + node_type, self.default_visit)
        return meth(node)

    def default_visit(self, node):
        node_type = node.__class__.__name__
        # Add node type
        args = {
            self.ast_type_field: node_type
        }
        # Visit fields
        for field in node._fields:
            assert field != self.ast_type_field
            meth = getattr(
                self, "visit_field_" + node_type + "_" + field,
                self.default_visit_field
            )
            args[field] = meth(getattr(node, field))
        # Visit attributes
        for attr in node._attributes:
            assert attr != self.ast_type_field
            meth = getattr(
                self, "visit_attribute_" + node_type + "_" + attr,
                self.default_visit_field
            )
            # Use None as default when lineno/col_offset are not set
            args[attr] = meth(getattr(node, attr, None))
        return args

    def default_visit_field(self, val):
        if isinstance(val, ast.AST):
            return self.visit(val)
        if isinstance(val, (list, tuple)):
            return [self.visit(x) for x in val]
        return val

    # Special visitors

    def visit_str(self, val):
        return str(val)

    def visit_Bytes(self, val):
        return str(val.s)

    def visit_NoneType(self, val):
        del val  # Unused
        return None

    def visit_field_NameConstant_value(self, val):
        return str(val)

    def visit_field_Num_n(self, val):
        if isinstance(val, int):
            return {
                self.ast_type_field: "int",
                "n": val,
                # JavaScript integers are limited to 2**53 - 1 bits,
                # so we add a string representation of the integer
                "n_str": str(val),
            }
        if isinstance(val, float):
            return {
                self.ast_type_field: "float",
                "n": val
            }
        if isinstance(val, complex):
            return {
                self.ast_type_field: "complex",
                "n": val.real,
                "i": val.imag
            }
