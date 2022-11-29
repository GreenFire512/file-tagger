import React from 'react';
import { Tree } from 'antd';

class TagTreeWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
        data: null
    };
    this.refresh();
  }

  refresh() {
    fetch('/api/tags/tree')
      .then(response => {
        response.json().then(data => (this.setState({ data })))
      })
  }

  onSelect = (selectedKeys, info) => {
    console.log('selected', selectedKeys, info);
  };

  onDoubleClick = (selectedKeys, key) => {
    this.props.addTagToSearch(key);
  }

  dataToTree() {
    let tree = [];
    Object.keys(this.state.data).map(group => {
      let children = [];
      if (Object.keys(this.state.data[group]).length > 0) {
        Object.keys(this.state.data[group]).map(tag => {
          children.push({ title: tag, key: group + tag});
        });
        tree.push({title: group , key: group, children: children});
      } else {
        tree.push({title: group , key: group});
      }
      
    })
    return tree;
  }
  
  render() {
    if (this.state.data) {
      const treeData = this.dataToTree();
      return (<div>
        <h1>Tag Tree</h1>
        <Tree
          treeData={treeData}
          showLine={{showLeafIcon: false}}
          showIcon={false}
          multiple
          onDoubleClick={this.onDoubleClick}
          onSelect={this.onSelect}
        />
      </div>)
    }
    return (
      <div>
        {'Loading...'}
      </div>
    );
  }
}

export default TagTreeWidget;