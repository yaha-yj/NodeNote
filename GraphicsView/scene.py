from collections import OrderedDict
from PyQt5 import QtWidgets, QtCore
from Components import effect_background, effect_cutline, attribute, pipe, container, port
from Model import serializable, constants

__all__ = ["Scene"]


class Scene(QtWidgets.QGraphicsScene, serializable.Serializable):
    def __init__(self, sub_scene_flag, view, attribute_widget=None, parent=None):
        super(Scene, self).__init__(parent)
        self.view = view
        self.attribute_widget = attribute_widget
        self.setSceneRect(QtCore.QRectF())
        self.sub_scene_flag = sub_scene_flag

        # background image
        self.background_image = effect_background.EffectBackground(self.view)
        self.background_image.resize(self.view.size().width(), self.view.size().height())
        self.background_image.setPos(self.view.mapToScene(0, 0).x(), self.view.mapToScene(0, 0).y())
        self.addItem(self.background_image)
        self.background_image.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)

        # CUT LINE
        self.cutline = effect_cutline.EffectCutline()
        self.addItem(self.cutline)

    def get_id_attribute(self, attribute_id) -> attribute.AttributeWidget:
        for item in self.items():
            if isinstance(item, attribute.AttributeWidget):
                if item.id == attribute_id:
                    return item

    def get_id_logic(self, logic_id) -> attribute.LogicWidget:
        for item in self.items():
            if isinstance(item, attribute.LogicWidget):
                if item.id == logic_id:
                    return item

    def get_id_port(self, port_id) -> port.Port:
        for item in self.items():
            if isinstance(item, attribute.AttributeWidget):
                if item.true_input_port.id == port_id:
                    return item.true_input_port
                elif item.false_input_port.id == port_id:
                    return item.false_input_port
                elif item.true_output_port.id == port_id:
                    return item.true_output_port
                elif item.false_output_port.id == port_id:
                    return item.false_output_port
            elif isinstance(item, attribute.LogicWidget):
                if item.input_port.id == port_id:
                    return item.input_port
                elif item.output_port.id == port_id:
                    return item.output_port

    def get_id_pipe(self, pipe_id) -> pipe.Pipe:
        for item in self.items():
            if isinstance(item, pipe.Pipe):
                if item.id == pipe_id:
                    return item

    def serialize(self):
        attribute_widgets = list()
        logic_widgets = list()
        pipe_widgets = list()
        container_widgets = list()

        for item in self.items():
            if isinstance(item, attribute.AttributeWidget):
                attribute_widgets.append(item.serialize())
            elif isinstance(item, attribute.LogicWidget):
                logic_widgets.append(item.serialize())
            elif isinstance(item, pipe.Pipe):
                pipe_widgets.append(item.serialize())
            elif isinstance(item, container.Container):
                container_widgets.append(item.serialize())

        return OrderedDict([
            ('id', self.id),
            ('attribute widgets', attribute_widgets),
            ('logic widgets', logic_widgets),
            ('pipe widgets', pipe_widgets),
            ('container widgets', container_widgets)
        ])

    def deserialize(self, data, hashmap: dict, view=None, flag=True):
        if flag is True:
            # deserialize id
            self.id = data['id']
            hashmap[data['id']] = self
            # deserialize attribute widgets with (id, geometry)
            for attribute_data in data['attribute widgets']:
                attribute.AttributeWidget().deserialize(attribute_data, hashmap, view, flag=True)
            # deserialize logic widgets with (id, geometry)
            for logic_data in data['logic widgets']:
                attribute.LogicWidget().deserialize(logic_data, hashmap, view, flag=True)
            # deserialize pipe widgets with all
            for pipe_data in data['pipe widgets']:
                start_port = self.get_id_port(pipe_data['start port'])
                if constants.DEBUG_DESERIALIZE:
                    print("find start port: ", start_port,
                          "\nstart port id: ", pipe_data['start port'])
                end_port = self.get_id_port(pipe_data['end port'])
                pipe.Pipe(start_port, end_port, None).deserialize(pipe_data, hashmap, view, flag=True)
                start_port.update_pipes_position()
                end_port.update_pipes_position()
        elif flag is False:
            for item in self.items():
                # deserialize attribute widgets second time
                if isinstance(item, attribute.AttributeWidget):
                    # deserialize attribute widgets with attribute sub widgets
                    for attribute_widget_data in data['attribute widgets']:
                        # traverse list and find right attribute
                        if item.id == attribute_widget_data['id']:
                            for attribute_sub_id in attribute_widget_data['attribute sub widgets']:
                                sub_attribute_widget = self.get_id_attribute(attribute_sub_id)
                                item.attribute_sub_widgets.append(sub_attribute_widget)
                                item.attribute_layout.addItem(sub_attribute_widget)
                            # deserialize attribute widgets with attribute next widgets
                            for attribute_next_id in attribute_widget_data['next attribute widgets']:
                                next_attribute_widget = self.get_id_attribute(attribute_next_id)
                                item.next_attribute.append(next_attribute_widget)
                                if constants.DEBUG_DESERIALIZE:
                                    print("deserialize attribute widget: ", item,
                                          "add next attribute: ", next_attribute_widget,
                                          "current next attribute: ", item.next_attribute)
                            # deserialize attribute widgets with attribute last widgets
                            for attribute_last_id in attribute_widget_data['last attribute widgets']:
                                last_attribute_widget = self.get_id_attribute(attribute_last_id)
                                item.last_attribute.append(last_attribute_widget)
                                if constants.DEBUG_DESERIALIZE:
                                    print("deserialize attribute widget: ", item,
                                          "add last attribute: ", last_attribute_widget,
                                          "current last attribute: ", item.last_attribute)
                            # deserialize attribute widgets with logic next widgets
                            for logic_next_id in attribute_widget_data['next logic widgets']:
                                next_logic_widget = self.get_id_logic(logic_next_id)
                                item.next_logic.append(next_logic_widget)
                            # deserialize attribute widgets with logic next widgets
                            for logic_last_id in attribute_widget_data['last logic widgets']:
                                last_logic_widget = self.get_id_logic(logic_last_id)
                                item.last_logic.append(last_logic_widget)
                            # deserialize attribute widgets with pipes
                            for pipe_id in attribute_widget_data['input true port']['pipes']:
                                pipe_widget = self.get_id_pipe(pipe_id)
                                item.true_input_port.pipes.append(pipe_widget)
                                item.update_pipe_position()
                            for pipe_id in attribute_widget_data['input false port']['pipes']:
                                pipe_widget = self.get_id_pipe(pipe_id)
                                item.false_input_port.pipes.append(pipe_widget)
                                item.update_pipe_position()
                            for pipe_id in attribute_widget_data['output true port']['pipes']:
                                pipe_widget = self.get_id_pipe(pipe_id)
                                item.true_output_port.pipes.append(pipe_widget)
                                item.update_pipe_position()
                            for pipe_id in attribute_widget_data['output false port']['pipes']:
                                pipe_widget = self.get_id_pipe(pipe_id)
                                item.false_output_port.pipes.append(pipe_widget)
                                item.update_pipe_position()
            # deserialize logic widgets second time
                elif isinstance(item, attribute.LogicWidget):
                    for logic_widget_data in data['logic widgets']:
                        # traverse list and find right logic
                        if item.id == logic_widget_data['id']:
                            # deserialize logic widgets with attribute next widgets
                            for attribute_next_id in logic_widget_data['next attribute widgets']:
                                next_attribute_widget = self.get_id_attribute(attribute_next_id)
                                item.next_attribute.append(next_attribute_widget)
                            # deserialize logic widgets with attribute last widgets
                            for attribute_last_id in logic_widget_data['last attribute widgets']:
                                last_attribute_widget = self.get_id_attribute(attribute_last_id)
                                item.last_attribute.append(last_attribute_widget)
                            # deserialize logic widgets with logic next widgets
                            for logic_next_id in logic_widget_data['next logic widgets']:
                                next_logic_widget = self.get_id_logic(logic_next_id)
                                item.next_logic.append(next_logic_widget)
                            # deserialize logic widgets with logic last widgets
                            for logic_last_id in logic_widget_data['last logic widgets']:
                                last_logic_widget = self.get_id_logic(logic_last_id)
                                item.last_logic.append(last_logic_widget)
                            # deserialize logic widgets with ports
                            for pipe_id in logic_widget_data['input port']['pipes']:
                                pipe_widget = self.get_id_pipe(pipe_id)
                                item.input_port.pipes.append(pipe_widget)
                                item.update_pipe_position()
                            for pipe_id in logic_widget_data['output port']['pipes']:
                                pipe_widget = self.get_id_pipe(pipe_id)
                                item.output_port.pipes.append(pipe_widget)
                                item.update_pipe_position()
        return True
