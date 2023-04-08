import { List } from 'antd';

export default function FileWidget() {
  return (
    <div>
      <List
        loading={this.props.list == null}
        header={<div>Tag Search</div>}
        bordered
        dataSource={this.props.list}
        renderItem={item => <List.Item>{item}</List.Item>}
      />
    </div>
  );
}