import { Checkbox } from 'antd'
import './check-box.style.css'

type Props = {
  onClick?: () => void
}
const AppCheckbox = ({ onClick }: Props) => {
  return <Checkbox onClick={onClick} className='custom-checkbox' />
}
export default AppCheckbox
